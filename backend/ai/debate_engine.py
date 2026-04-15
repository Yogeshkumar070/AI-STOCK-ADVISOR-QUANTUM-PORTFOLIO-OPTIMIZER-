from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
import yfinance as yf

from backend.ai.forecaster import run_forecast
from backend.ai.llm_support import get_openai_client, run_json_prompt
from backend.ai.mcs_engine import calculate_management_score


def _safe_ticker(symbol: str) -> yf.Ticker:
    ticker_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
    return yf.Ticker(ticker_symbol)


def _compute_rsi(closes: np.ndarray, period: int = 14) -> float | None:
    if len(closes) <= period:
        return None

    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def _score_value(value: float, thresholds: list[tuple[float, int]], reverse: bool = False, default: int = 50) -> int:
    if value is None:
        return default

    if reverse:
        for threshold, score in thresholds:
            if value <= threshold:
                return score
        return thresholds[-1][1]

    for threshold, score in thresholds:
        if value >= threshold:
            return score
    return thresholds[-1][1]


def _pillar(title: str, argument: str, evidence: str, score: int, quality: str = "high") -> dict[str, Any]:
    return {
        "title": title,
        "argument": argument,
        "evidence": evidence,
        "score": max(1, min(100, int(score))),
        "data_quality": quality,
    }


def _build_snapshot(symbol: str) -> dict[str, Any]:
    ticker = _safe_ticker(symbol)
    info = ticker.info
    history = ticker.history(period="1y")

    if history.empty:
        raise ValueError(f"No price history found for {symbol}")

    closes = history["Close"].astype(float).values
    current_price = float(closes[-1])
    sma_50 = float(np.mean(closes[-50:])) if len(closes) >= 50 else current_price
    sma_200 = float(np.mean(closes[-200:])) if len(closes) >= 200 else current_price
    return_6m = float(((current_price / closes[-126]) - 1) * 100) if len(closes) >= 126 else float(((current_price / closes[0]) - 1) * 100)
    annualized_vol = float(np.std(np.diff(np.log(closes))) * np.sqrt(252) * 100) if len(closes) > 2 else 0.0
    rsi_14 = _compute_rsi(closes)

    return {
        "symbol": symbol.upper(),
        "company_name": info.get("longName") or info.get("shortName") or symbol.upper(),
        "sector": info.get("sector") or "Unknown",
        "industry": info.get("industry") or "Unknown",
        "current_price": round(current_price, 2),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "profit_margin": info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins"),
        "dividend_yield": info.get("dividendYield"),
        "sma_50": round(sma_50, 2),
        "sma_200": round(sma_200, 2),
        "return_6m": round(return_6m, 2),
        "annualized_vol": round(annualized_vol, 2),
        "rsi_14": round(rsi_14, 2) if rsi_14 is not None else None,
        "above_sma_50": current_price > sma_50,
        "above_sma_200": current_price > sma_200,
    }


def _build_bull_case(snapshot: dict[str, Any], mcs: dict[str, Any], forecast: dict[str, Any]) -> list[dict[str, Any]]:
    pillars: list[dict[str, Any]] = []
    revenue_growth = snapshot.get("revenue_growth")
    roe = snapshot.get("roe")
    return_6m = snapshot.get("return_6m")
    pe_ratio = snapshot.get("pe_ratio")
    expected_return = forecast["metrics"]["expected_return_2y"]
    profit_probability = forecast["probability"]["profit"]

    if revenue_growth is not None or forecast["metrics"]["expected_return_2y"] > 0:
        rg_pct = f"{revenue_growth * 100:.1f}%" if revenue_growth is not None else "positive"
        score = _score_value(revenue_growth or 0.0, [(0.15, 88), (0.08, 77), (0.03, 65), (-1, 48)])
        pillars.append(_pillar(
            "Growth runway",
            "The bull case rests on a still-constructive growth setup with room for operating leverage.",
            f"Revenue growth is {rg_pct} and the model still sees {expected_return:.1f}% expected 2Y return.",
            score,
        ))

    if roe is not None:
        score = _score_value(roe, [(0.22, 90), (0.16, 80), (0.10, 68), (-1, 50)])
        pillars.append(_pillar(
            "Capital efficiency",
            "High return on equity suggests the business can compound without stretching capital too hard.",
            f"ROE stands at {roe * 100:.1f}% with profit probability at {profit_probability:.1f}%.",
            score,
        ))

    if snapshot["above_sma_50"] or snapshot["above_sma_200"] or (return_6m is not None and return_6m > 0):
        score = 82 if snapshot["above_sma_200"] else 70
        pillars.append(_pillar(
            "Trend support",
            "Price structure is not fighting the thesis, which matters when conviction needs market confirmation.",
            f"6M return is {return_6m:.1f}% and price is {'above' if snapshot['above_sma_200'] else 'below'} the 200-day average.",
            score,
            "medium",
        ))

    if mcs["score"] >= 60:
        pillars.append(_pillar(
            "Management trust",
            "Execution credibility strengthens the bullish case because forward guidance carries more weight.",
            f"MCS is {mcs['score']}/100 with {mcs['trust_level'].lower()} trust and {mcs['delivered_quarters']} delivered guidance calls.",
            76 if mcs["score"] < 75 else 88,
        ))

    if pe_ratio is not None and roe is not None and pe_ratio < 35 and roe > 0.14:
        pillars.append(_pillar(
            "Valuation still defendable",
            "The multiple is not obviously reckless relative to business quality.",
            f"P/E is {pe_ratio:.1f}x while ROE is {roe * 100:.1f}%, keeping the premium more explainable than speculative.",
            71,
            "medium",
        ))

    if not pillars:
        pillars.append(_pillar(
            "Residual upside",
            "There is still a modest bull case, but the evidence is less decisive than ideal.",
            f"Profit probability is {profit_probability:.1f}% with current price at Rs {snapshot['current_price']:.2f}.",
            56,
            "medium",
        ))

    return sorted(pillars, key=lambda item: item["score"], reverse=True)[:4]


def _build_bear_case(snapshot: dict[str, Any], mcs: dict[str, Any], forecast: dict[str, Any]) -> list[dict[str, Any]]:
    pillars: list[dict[str, Any]] = []
    pe_ratio = snapshot.get("pe_ratio")
    debt_to_equity = snapshot.get("debt_to_equity")
    annualized_vol = snapshot.get("annualized_vol")
    rsi_14 = snapshot.get("rsi_14")
    expected_return = forecast["metrics"]["expected_return_2y"]
    loss_probability = forecast["probability"]["loss_20pct"]

    if pe_ratio is not None:
        score = _score_value(pe_ratio, [(45, 88), (32, 76), (24, 60), (-1, 44)])
        if score >= 60:
            pillars.append(_pillar(
                "Valuation risk",
                "The market may already be discounting a lot of the good news, leaving less room for mistakes.",
                f"P/E sits at {pe_ratio:.1f}x, which raises downside sensitivity if growth cools.",
                score,
            ))

    if mcs["score"] < 65:
        pillars.append(_pillar(
            "Guidance credibility drag",
            "A weaker management delivery record makes future promises less investable.",
            f"MCS is only {mcs['score']}/100 and overpromising flags total {mcs['overpromised_quarters']} quarters.",
            82 if mcs["score"] < 50 else 68,
        ))

    if debt_to_equity is not None:
        score = _score_value(debt_to_equity, [(150, 85), (100, 74), (60, 62), (-1, 42)])
        if score >= 60:
            pillars.append(_pillar(
                "Balance-sheet pressure",
                "Higher leverage narrows the margin for execution errors or macro stress.",
                f"Debt to equity is {debt_to_equity:.1f}, which can amplify volatility in tougher cycles.",
                score,
                "medium",
            ))

    if not snapshot["above_sma_200"] or expected_return < 5:
        score = 79 if not snapshot["above_sma_200"] else 64
        pillars.append(_pillar(
            "Weak technical confirmation",
            "The bear case is stronger when the tape is not validating the narrative.",
            f"Price is {'below' if not snapshot['above_sma_200'] else 'above'} the 200-day average and expected 2Y return is {expected_return:.1f}%.",
            score,
            "medium",
        ))

    if annualized_vol is not None and annualized_vol > 30:
        pillars.append(_pillar(
            "Volatility tax",
            "High volatility can erode conviction even if the long-term thesis survives.",
            f"Annualized volatility is {annualized_vol:.1f}% and the modeled chance of a 20% drawdown is {loss_probability:.1f}%.",
            72,
            "medium",
        ))

    if rsi_14 is not None and rsi_14 > 68:
        pillars.append(_pillar(
            "Near-term overheating",
            "Momentum can become fragile when the stock is already extended.",
            f"RSI(14) is {rsi_14:.1f}, which points to a crowded short-term setup.",
            66,
            "medium",
        ))

    if not pillars:
        pillars.append(_pillar(
            "Limited edge",
            "The bear case is weaker here, but the stock still needs cleaner evidence for a high-conviction long.",
            f"Modeled downside probability is {loss_probability:.1f}%.",
            48,
            "medium",
        ))

    return sorted(pillars, key=lambda item: item["score"], reverse=True)[:4]


def _build_rebuttal(bull_case: list[dict[str, Any]], bear_case: list[dict[str, Any]], mcs: dict[str, Any], forecast: dict[str, Any]) -> dict[str, list[str]]:
    top_bull = bull_case[0]
    top_bear = bear_case[0]
    bull_rebuttal = [
        f"The main bear point is {top_bear['title'].lower()}, but it is partially offset by {top_bull['title'].lower()}.",
        f"Management credibility at {mcs['score']}/100 reduces the chance that the market is relying on empty guidance." if mcs["score"] >= 60
        else f"Management credibility is only moderate, so the bull case should lean more on hard operating data than on guidance.",
    ]
    bear_rebuttal = [
        f"The top bull pillar is {top_bull['title'].lower()}, but that strength may already be priced in if expectations stay elevated.",
        f"The forecast still leaves a {forecast['probability']['loss_20pct']:.1f}% chance of a 20%+ drawdown, so conviction should not ignore path risk.",
    ]
    return {
        "bull_rebuttal": bull_rebuttal,
        "bear_rebuttal": bear_rebuttal,
    }


def _final_verdict(bull_case: list[dict[str, Any]], bear_case: list[dict[str, Any]], mcs: dict[str, Any], forecast: dict[str, Any]) -> dict[str, Any]:
    bull_score = round(sum(item["score"] for item in bull_case) / len(bull_case))
    bear_score = round(sum(item["score"] for item in bear_case) / len(bear_case))
    balance = bull_score - bear_score
    conviction = max(1, min(100, round(50 + balance * 0.9 + (mcs["score"] - 50) * 0.2)))
    confidence = max(40, min(94, round(55 + abs(balance) * 0.5)))

    if conviction >= 74:
        action = "BUY"
        winner = "bull"
    elif conviction <= 42:
        action = "AVOID"
        winner = "bear"
    else:
        action = "HOLD"
        winner = "balanced"

    top_driver = bull_case[0]["title"] if winner == "bull" else bear_case[0]["title"] if winner == "bear" else "Mixed evidence"
    rationale = (
        f"Bull arguments average {bull_score}/100 versus {bear_score}/100 for the bear case. "
        f"MCS at {mcs['score']}/100 and forecast profit probability at {forecast['probability']['profit']:.1f}% shape the final stance."
    )

    return {
        "action": action,
        "winner": winner,
        "conviction_score": conviction,
        "confidence": confidence,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "key_driver": top_driver,
        "rationale": rationale,
        "caution": bear_case[0]["argument"],
    }


def _llm_polish(payload: dict[str, Any]) -> dict[str, Any] | None:
    if get_openai_client() is None:
        return None
    system_prompt = (
        "You are a disciplined equity research debate engine. "
        "Keep the same facts, stay concise, and return valid JSON only."
    )
    user_prompt = (
        "Improve the language of this structured stock debate without inventing facts. "
        "Preserve all keys. Keep arguments crisp, specific, and institutional.\n\n"
        f"{payload}"
    )
    return run_json_prompt(system_prompt, user_prompt)


def run_debate(symbol: str) -> dict[str, Any]:
    snapshot = _build_snapshot(symbol.upper())
    mcs = calculate_management_score(symbol.upper())
    forecast = run_forecast(symbol.upper())

    bull_case = _build_bull_case(snapshot, mcs, forecast)
    bear_case = _build_bear_case(snapshot, mcs, forecast)
    rebuttal = _build_rebuttal(bull_case, bear_case, mcs, forecast)
    verdict = _final_verdict(bull_case, bear_case, mcs, forecast)

    debate_payload = {
        "metadata": {
            "symbol": snapshot["symbol"],
            "company_name": snapshot["company_name"],
            "sector": snapshot["sector"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_mode": "hybrid_llm" if get_openai_client() is not None else "deterministic",
        },
        "inputs": {
            "current_price": snapshot["current_price"],
            "pe_ratio": snapshot["pe_ratio"],
            "roe": snapshot["roe"],
            "debt_to_equity": snapshot["debt_to_equity"],
            "revenue_growth": snapshot["revenue_growth"],
            "earnings_growth": snapshot["earnings_growth"],
            "rsi_14": snapshot["rsi_14"],
            "sma_50": snapshot["sma_50"],
            "sma_200": snapshot["sma_200"],
            "return_6m": snapshot["return_6m"],
            "annualized_vol": snapshot["annualized_vol"],
            "mcs_score": mcs["score"],
            "forecast_profit_probability": forecast["probability"]["profit"],
            "forecast_expected_return_2y": forecast["metrics"]["expected_return_2y"],
        },
        "bull_case": {
            "summary": bull_case[0]["argument"],
            "score": verdict["bull_score"],
            "pillars": bull_case,
        },
        "bear_case": {
            "summary": bear_case[0]["argument"],
            "score": verdict["bear_score"],
            "pillars": bear_case,
        },
        "rebuttal": rebuttal,
        "verdict": verdict,
        "risk_flags": [item["title"] for item in bear_case[:3]],
        "opportunity_flags": [item["title"] for item in bull_case[:3]],
        "mcs_summary": {
            "score": mcs["score"],
            "trust_level": mcs["trust_level"],
            "evidence_mode": mcs["evidence_mode"],
            "insight": mcs["insight"],
        },
    }

    polished = _llm_polish(debate_payload)
    if isinstance(polished, dict):
        polished.setdefault("metadata", debate_payload["metadata"])
        polished["metadata"]["model_mode"] = "hybrid_llm"
        return polished

    return debate_payload
