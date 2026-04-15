from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import yfinance as yf

from backend.ai.llm_support import get_openai_client, run_json_prompt


GUIDANCE_DIR = Path(__file__).resolve().parents[1] / "data" / "management_guidance"


def _safe(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    try:
        if isinstance(value, float) and np.isnan(value):
            return default
    except (TypeError, ValueError):
        return default
    return value


def _ticker(symbol: str) -> yf.Ticker:
    ticker_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
    return yf.Ticker(ticker_symbol)


def _get_market_data(symbol: str) -> dict[str, Any]:
    ticker = _ticker(symbol)
    info = ticker.info

    earnings = []
    try:
        earnings_history = ticker.earnings_history
        if earnings_history is not None and not earnings_history.empty:
            for idx, row in earnings_history.iterrows():
                earnings.append(
                    {
                        "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                        "eps_actual": _safe(row.get("epsActual")),
                        "eps_estimate": _safe(row.get("epsEstimate")),
                        "surprise_pct": _safe(row.get("surprisePercent")),
                    }
                )
    except Exception:
        pass

    quarterly_revenue = []
    try:
        quarterly_stmt = ticker.quarterly_income_stmt
        if quarterly_stmt is not None and not quarterly_stmt.empty and "Total Revenue" in quarterly_stmt.index:
            for col in list(quarterly_stmt.columns)[:8]:
                value = quarterly_stmt.loc["Total Revenue", col]
                quarterly_revenue.append(
                    {
                        "period": str(col.date()) if hasattr(col, "date") else str(col),
                        "revenue": float(value) if _safe(value) is not None else None,
                    }
                )
    except Exception:
        pass

    return {
        "company_name": info.get("longName") or info.get("shortName") or symbol,
        "sector": info.get("sector", "Unknown"),
        "industry": info.get("industry", "Unknown"),
        "earnings": earnings,
        "quarterly_revenue": quarterly_revenue,
        "pe": _safe(info.get("trailingPE")),
        "forward_pe": _safe(info.get("forwardPE")),
        "roe": _safe(info.get("returnOnEquity")),
        "de": _safe(info.get("debtToEquity")),
        "rev_growth": _safe(info.get("revenueGrowth")),
        "earn_growth": _safe(info.get("earningsGrowth")),
        "profit_margins": _safe(info.get("profitMargins")),
        "op_margins": _safe(info.get("operatingMargins")),
        "rec_mean": _safe(info.get("recommendationMean")),
        "current_price": _safe(info.get("currentPrice")),
        "target_mean": _safe(info.get("targetMeanPrice")),
        "eps": _safe(info.get("trailingEps")),
        "forward_eps": _safe(info.get("forwardEps")),
    }


def _load_guidance_history(symbol: str) -> dict[str, Any] | None:
    path = GUIDANCE_DIR / f"{symbol.upper()}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _heuristic_guidance_score(item: dict[str, Any]) -> dict[str, Any]:
    delivered = item.get("delivered")
    actual_value = item.get("actual_value")
    target_value = item.get("target_value")
    direction = (item.get("direction") or "").lower()
    actual_text = item.get("actual_text") or "Actual outcome unavailable"

    if delivered is None and target_value is not None and actual_value is not None:
        try:
            target_value = float(target_value)
            actual_value = float(actual_value)
            delivered = actual_value >= target_value if direction not in {"decrease", "reduce"} else actual_value <= target_value
        except (TypeError, ValueError):
            delivered = None

    if delivered is None and actual_value is not None:
        try:
            actual_numeric = float(actual_value)
            if direction in {"increase", "improve", "grow", "expand", "maintain"}:
                delivered = actual_numeric >= 0
            elif direction in {"decrease", "reduce"}:
                delivered = actual_numeric <= 0
        except (TypeError, ValueError):
            delivered = None

    if delivered is True:
        score = 84
        verdict = "Delivered"
        reason = f"Management guidance was broadly delivered. {actual_text}"
    elif delivered is False:
        score = 32
        verdict = "Missed"
        reason = f"Management over-promised versus reported outcomes. {actual_text}"
    else:
        score = 55
        verdict = "Mixed"
        reason = f"Guidance was only partially verifiable. {actual_text}"

    return {
        "quarter": item.get("quarter"),
        "statement": item.get("statement"),
        "metric": item.get("metric"),
        "target_text": item.get("target_text"),
        "actual_text": actual_text,
        "delivered": delivered,
        "score": score,
        "verdict": verdict,
        "reason": reason,
        "source": item.get("source", "local guidance dataset"),
    }


def _llm_guidance_score(item: dict[str, Any]) -> dict[str, Any] | None:
    if get_openai_client() is None:
        return None
    result = run_json_prompt(
        system_prompt="Score management guidance delivery. Return JSON with score, verdict, reason, delivered.",
        user_prompt=(
            f"Quarter: {item.get('quarter')}\n"
            f"Statement: {item.get('statement')}\n"
            f"Target context: {item.get('target_text')}\n"
            f"Actual outcome: {item.get('actual_text')}\n"
            f"Actual value: {item.get('actual_value')}\n"
            "Score 0-100 where 100 means clearly delivered."
        ),
    )
    if not isinstance(result, dict):
        return None
    return {
        "quarter": item.get("quarter"),
        "statement": item.get("statement"),
        "metric": item.get("metric"),
        "target_text": item.get("target_text"),
        "actual_text": item.get("actual_text"),
        "delivered": result.get("delivered"),
        "score": max(0, min(100, int(result.get("score", 55)))),
        "verdict": result.get("verdict", "Mixed"),
        "reason": result.get("reason", "No explanation returned."),
        "source": item.get("source", "local guidance dataset"),
    }


def _score_earnings(earnings: list[dict[str, Any]]) -> tuple[int, str, str, list[dict[str, Any]]]:
    valid = [entry for entry in earnings if entry["surprise_pct"] is not None]
    if not valid:
        return 50, "N/A", "0.0%", []
    beats = sum(1 for entry in valid if entry["surprise_pct"] > 0)
    total = len(valid)
    beat_rate = beats / total
    avg_surprise = float(np.mean([entry["surprise_pct"] for entry in valid]))
    score = int(beat_rate * 70 + min(max(avg_surprise * 3, -30), 30))
    score = max(0, min(100, score))
    timeline = []
    for entry in valid[:8]:
        status = "BEAT" if entry["surprise_pct"] > 1 else "MET" if abs(entry["surprise_pct"]) <= 1 else "MISSED"
        timeline.append(
            {
                "date": entry["date"],
                "eps_actual": entry["eps_actual"],
                "eps_estimate": entry["eps_estimate"],
                "surprise_pct": round(entry["surprise_pct"], 2),
                "status": status,
            }
        )
    return score, f"{beats} out of {total} quarters beat estimates", f"{avg_surprise:+.1f}%", timeline


def _score_revenue(quarterly_revenue: list[dict[str, Any]]) -> tuple[int, list[dict[str, Any]]]:
    valid = [entry for entry in quarterly_revenue if entry["revenue"] is not None]
    if len(valid) < 2:
        return 50, []
    revenues = list(reversed([entry["revenue"] for entry in valid]))
    periods = list(reversed([entry["period"] for entry in valid]))
    up_quarters = sum(1 for idx in range(1, len(revenues)) if revenues[idx] > revenues[idx - 1])
    growth_rate = up_quarters / (len(revenues) - 1)
    total_growth = (revenues[-1] - revenues[0]) / abs(revenues[0]) if revenues[0] else 0
    score = int(growth_rate * 60 + min(max(total_growth * 100, -40), 40))
    score = max(0, min(100, score))
    trend = []
    for idx, revenue in enumerate(revenues):
        previous = revenues[idx - 1] if idx > 0 else None
        growth_qoq = ((revenue - previous) / abs(previous) * 100) if previous else 0
        trend.append({"period": periods[idx], "revenue": round(revenue / 1e7, 2), "growth_qoq": round(growth_qoq, 1)})
    return score, trend


def _score_discipline(data: dict[str, Any]) -> int:
    scores = []
    if data["roe"] is not None:
        scores.append(95 if data["roe"] >= 0.20 else 78 if data["roe"] >= 0.15 else 60 if data["roe"] >= 0.10 else 40 if data["roe"] >= 0.05 else 20)
    if data["profit_margins"] is not None:
        scores.append(92 if data["profit_margins"] >= 0.20 else 72 if data["profit_margins"] >= 0.12 else 50 if data["profit_margins"] >= 0.05 else 25)
    if data["de"] is not None:
        scores.append(95 if data["de"] <= 20 else 80 if data["de"] <= 50 else 55 if data["de"] <= 100 else 35 if data["de"] <= 150 else 15)
    if data["op_margins"] is not None:
        scores.append(90 if data["op_margins"] >= 0.25 else 72 if data["op_margins"] >= 0.15 else 50 if data["op_margins"] >= 0.08 else 28)
    return int(np.mean(scores)) if scores else 50


def _score_analyst(data: dict[str, Any]) -> int:
    scores = []
    if data["rec_mean"] is not None:
        scores.append(max(0, min(100, int((5 - data["rec_mean"]) / 4 * 100))))
    if data["current_price"] and data["target_mean"] and data["current_price"] > 0:
        upside = (data["target_mean"] - data["current_price"]) / data["current_price"]
        scores.append(max(0, min(100, int(50 + upside * 200))))
    return int(np.mean(scores)) if scores else 50


def _verdict(score: int) -> str:
    if score >= 80:
        return "EXCELLENT"
    if score >= 65:
        return "STRONG"
    if score >= 45:
        return "MODERATE"
    if score >= 25:
        return "WEAK"
    return "POOR"


def _trend(earnings_delivery: int, revenue_consistency: int, data: dict[str, Any]) -> str:
    if data["earn_growth"] is not None and data["rev_growth"] is not None:
        if data["earn_growth"] > 0.05 and data["rev_growth"] > 0.05:
            return "IMPROVING"
        if data["earn_growth"] < -0.05 or data["rev_growth"] < -0.05:
            return "DETERIORATING"
    if earnings_delivery >= 65 and revenue_consistency >= 60:
        return "IMPROVING"
    if earnings_delivery < 40 or revenue_consistency < 40:
        return "DETERIORATING"
    return "STABLE"


def _guidance_summary(guidance_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not guidance_results:
        return {
            "guidance_accuracy_score": None,
            "delivered_quarters": 0,
            "overpromised_quarters": 0,
            "trust_meter": "Proxy mode",
            "evidence_mode": "market_proxy",
            "highlights": ["No local earnings-call guidance file found, so trust score leans on execution proxies."],
        }
    delivered = sum(1 for item in guidance_results if item["delivered"] is True)
    overpromised = sum(1 for item in guidance_results if item["delivered"] is False)
    guidance_score = round(sum(item["score"] for item in guidance_results) / len(guidance_results))
    trust_meter = "High" if guidance_score >= 75 else "Moderate" if guidance_score >= 55 else "Low"
    return {
        "guidance_accuracy_score": guidance_score,
        "delivered_quarters": delivered,
        "overpromised_quarters": overpromised,
        "trust_meter": trust_meter,
        "evidence_mode": "transcript_guidance",
        "highlights": [
            f"Delivered past guidance in {delivered}/{len(guidance_results)} tracked quarters.",
            f"Over-promised in {overpromised} quarter(s)." if overpromised else "No clear over-promise flags in the tracked sample.",
        ],
    }


def calculate_management_score(symbol: str) -> dict[str, Any]:
    data = _get_market_data(symbol)
    guidance_data = _load_guidance_history(symbol)
    guidance_items = guidance_data.get("history", []) if guidance_data else []
    guidance_results = []
    llm_used = False
    for item in guidance_items:
        llm_result = _llm_guidance_score(item)
        if llm_result is not None:
            guidance_results.append(llm_result)
            llm_used = True
        else:
            guidance_results.append(_heuristic_guidance_score(item))

    earnings_delivery_score, beat_rate, avg_surprise, timeline = _score_earnings(data["earnings"])
    revenue_consistency_score, revenue_trend = _score_revenue(data["quarterly_revenue"])
    financial_discipline_score = _score_discipline(data)
    analyst_confidence_score = _score_analyst(data)
    proxy_score = int(earnings_delivery_score * 0.30 + revenue_consistency_score * 0.25 + financial_discipline_score * 0.25 + analyst_confidence_score * 0.20)

    guidance_summary = _guidance_summary(guidance_results)
    overall_score = int(proxy_score * 0.45 + guidance_summary["guidance_accuracy_score"] * 0.55) if guidance_summary["guidance_accuracy_score"] is not None else proxy_score
    verdict = _verdict(overall_score)
    trend = _trend(earnings_delivery_score, revenue_consistency_score, data)
    trust_level = guidance_summary["trust_meter"] if guidance_summary["guidance_accuracy_score"] is not None else verdict.title()
    insight = (
        "Management slightly aggressive in projections."
        if guidance_summary["guidance_accuracy_score"] is not None and guidance_summary["guidance_accuracy_score"] < 60
        else "Management guidance has been reasonably investable versus reported outcomes."
        if guidance_summary["guidance_accuracy_score"] is not None
        else "Trust score is inferred from execution proxies until transcript guidance is added."
    )

    key_strengths = []
    if guidance_summary["guidance_accuracy_score"] is not None and guidance_summary["guidance_accuracy_score"] >= 70:
        key_strengths.append("Management has converted guidance into reported delivery with good consistency.")
    if earnings_delivery_score >= 70:
        key_strengths.append("Quarterly earnings have landed above consensus more often than not.")
    if data["roe"] is not None and data["roe"] >= 0.15:
        key_strengths.append(f"ROE of {data['roe'] * 100:.1f}% signals strong capital discipline.")
    if not key_strengths:
        key_strengths.append("Available evidence is mixed rather than decisively positive.")

    key_concerns = []
    if guidance_summary["overpromised_quarters"] > 0:
        key_concerns.append("Tracked earnings-call guidance includes over-promise episodes.")
    if data["pe"] is not None and data["pe"] > 45:
        key_concerns.append(f"P/E at {data['pe']:.1f}x leaves less room for execution mistakes.")
    if revenue_consistency_score < 45:
        key_concerns.append("Quarterly revenue delivery has been inconsistent.")
    if not key_concerns:
        key_concerns.append("No major management-quality red flags stand out in the current sample.")

    return {
        "score": overall_score,
        "mcs_score": overall_score,
        "verdict": verdict,
        "trust_level": trust_level,
        "earnings_delivery_score": earnings_delivery_score,
        "revenue_consistency_score": revenue_consistency_score,
        "financial_discipline_score": financial_discipline_score,
        "analyst_confidence_score": analyst_confidence_score,
        "guidance_accuracy_score": guidance_summary["guidance_accuracy_score"],
        "beat_rate": beat_rate,
        "avg_surprise_pct": avg_surprise,
        "key_strengths": key_strengths[:4],
        "key_concerns": key_concerns[:4],
        "credibility_summary": f"{data['company_name']} scores {overall_score}/100 on management credibility. Proxy execution score is {proxy_score}/100.",
        "trend": trend,
        "investor_note": insight,
        "insight": insight,
        "trust_meter": guidance_summary["trust_meter"],
        "delivered_quarters": guidance_summary["delivered_quarters"],
        "overpromised_quarters": guidance_summary["overpromised_quarters"],
        "guidance_highlights": guidance_summary["highlights"],
        "guidance_history": guidance_results,
        "earnings_timeline": timeline,
        "revenue_trend": revenue_trend,
        "current_price": data["current_price"],
        "target_mean_price": data["target_mean"],
        "company_name": data["company_name"],
        "sector": data["sector"],
        "industry": data["industry"],
        "evidence_mode": guidance_summary["evidence_mode"],
        "llm_used": llm_used,
        "snapshot": {
            "pe": data["pe"],
            "roe": round(data["roe"] * 100, 1) if data["roe"] is not None else None,
            "de": round(data["de"], 1) if data["de"] is not None else None,
            "profit_margins": round(data["profit_margins"] * 100, 1) if data["profit_margins"] is not None else None,
            "rev_growth": round(data["rev_growth"] * 100, 1) if data["rev_growth"] is not None else None,
            "earn_growth": round(data["earn_growth"] * 100, 1) if data["earn_growth"] is not None else None,
            "eps": data["eps"],
            "forward_eps": data["forward_eps"],
        },
    }
