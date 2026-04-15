"""
AI Forecaster Engine — Monte Carlo Simulation + Trend Analysis
No API required. Pure quantitative forecasting from historical data.
"""

import yfinance as yf
import numpy as np
from typing import Dict, Any

from backend.data.cache_db import get_cached_mcs


def calculate_ai_adjusted_forecast(ticker: str, baseline_projected_growth_pct: float):
    """
    Applies the Management Credibility Score as a discount to future projections.
    """
    cached_data = get_cached_mcs(ticker.upper().replace(".NS", ""))
    mcs_score = cached_data["mcs_score"] if cached_data else 50.0
    discount_factor = mcs_score / 100.0
    ai_adjusted_growth = baseline_projected_growth_pct * discount_factor

    return {
        "ticker": ticker,
        "baseline_growth_pct": baseline_projected_growth_pct,
        "mcs_discount_factor": round(discount_factor, 2),
        "ai_adjusted_growth_pct": round(ai_adjusted_growth, 2)
    }


def run_forecast(symbol: str) -> Dict[str, Any]:
    """
    Runs Monte Carlo simulation and trend analysis for price forecasting.
    Returns scenario projections, probability metrics, and simulation paths.
    """
    ts = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
    tk = yf.Ticker(ts)
    info = tk.info

    hist = tk.history(period="2y")
    if hist.empty or len(hist) < 60:
        raise ValueError(f"Insufficient historical data for {symbol}")

    closes = hist["Close"].values.astype(float)
    current_price = float(closes[-1])
    company_name = info.get("longName") or info.get("shortName") or symbol

    # ── Calculate Statistics ──
    log_returns = np.diff(np.log(closes))
    mu_daily = float(np.mean(log_returns))
    sigma_daily = float(np.std(log_returns))
    mu_annual = mu_daily * 252
    sigma_annual = sigma_daily * np.sqrt(252)

    # ── Monte Carlo Simulation ──
    n_sims = 500
    days_forward = 504  # ~2 years
    dt = 1 / 252

    np.random.seed(42)  # Reproducible
    paths = np.zeros((n_sims, days_forward + 1))
    paths[:, 0] = current_price

    for t in range(1, days_forward + 1):
        z = np.random.standard_normal(n_sims)
        paths[:, t] = paths[:, t - 1] * np.exp(
            (mu_daily - 0.5 * sigma_daily**2) * 1 + sigma_daily * z
        )

    # ── Extract Scenario Data ──
    def scenario_at(day_idx):
        col = paths[:, day_idx]
        return {
            "bull": round(float(np.percentile(col, 80)), 2),
            "base": round(float(np.percentile(col, 50)), 2),
            "bear": round(float(np.percentile(col, 20)), 2),
            "best": round(float(np.percentile(col, 95)), 2),
            "worst": round(float(np.percentile(col, 5)), 2),
        }

    baseline_3mo = scenario_at(63)
    baseline_6mo = scenario_at(126)
    baseline_1y = scenario_at(252)
    baseline_2y = scenario_at(504)

    final_prices = paths[:, -1]
    prob_profit = float((final_prices > current_price).sum() / n_sims * 100)
    prob_20_up = float((final_prices > current_price * 1.2).sum() / n_sims * 100)
    prob_20_down = float((final_prices < current_price * 0.8).sum() / n_sims * 100)
    expected_return = float(((np.median(final_prices) - current_price) / current_price) * 100)
    mcs_adjustment = calculate_ai_adjusted_forecast(symbol, expected_return)
    raw_score = mcs_adjustment["mcs_discount_factor"] * 100
    discount_factor = mcs_adjustment["mcs_discount_factor"]

    def adjust_scenario(scenario: Dict[str, float]) -> Dict[str, float]:
        adjusted = {}
        for key, value in scenario.items():
            projected_growth_pct = ((value - current_price) / current_price) * 100
            adjusted_growth_pct = projected_growth_pct * discount_factor
            adjusted[key] = round(current_price * (1 + (adjusted_growth_pct / 100)), 2)
        return adjusted

    at_3mo = adjust_scenario(baseline_3mo)
    at_6mo = adjust_scenario(baseline_6mo)
    at_1y = adjust_scenario(baseline_1y)
    at_2y = adjust_scenario(baseline_2y)

    # ── Confidence Cone (sampled paths for chart) ──
    sample_days = list(range(0, days_forward + 1, 5))  # Every 5 days
    cone = []
    for d in sample_days:
        col = paths[:, d]
        cone.append({
            "day": d,
            "p5": round(float(np.percentile(col, 5)), 2),
            "p20": round(float(np.percentile(col, 20)), 2),
            "p50": round(float(np.percentile(col, 50)), 2),
            "p80": round(float(np.percentile(col, 80)), 2),
            "p95": round(float(np.percentile(col, 95)), 2),
        })

    # ── Trend Indicators ──
    sma_50 = float(np.mean(closes[-50:])) if len(closes) >= 50 else current_price
    sma_200 = float(np.mean(closes[-200:])) if len(closes) >= 200 else current_price
    above_sma50 = current_price > sma_50
    above_sma200 = current_price > sma_200
    golden_cross = sma_50 > sma_200

    # 1-year return
    if len(closes) >= 252:
        ret_1y = ((closes[-1] - closes[-252]) / closes[-252]) * 100
    else:
        ret_1y = ((closes[-1] - closes[0]) / closes[0]) * 100

    # ── AI Verdict ──
    if prob_profit > 65 and expected_return > 15 and golden_cross:
        verdict = "STRONG BUY"
        verdict_text = f"Monte Carlo projects {prob_profit:.0f}% probability of profit with {expected_return:.0f}% expected return. Golden cross and strong momentum support the bullish outlook."
    elif prob_profit > 55 and expected_return > 5:
        verdict = "BUY"
        verdict_text = f"Favorable risk-reward with {prob_profit:.0f}% profit probability. Base-case return of {expected_return:.0f}% is above market average."
    elif prob_profit > 45:
        verdict = "HOLD"
        verdict_text = f"Mixed signals with {prob_profit:.0f}% profit probability. Expected return of {expected_return:.0f}% is moderate. Wait for clearer directional signal."
    elif prob_profit > 35:
        verdict = "REDUCE"
        verdict_text = f"Below-average {prob_profit:.0f}% profit probability with {expected_return:.0f}% expected return. Consider reducing exposure."
    else:
        verdict = "SELL"
        verdict_text = f"Only {prob_profit:.0f}% probability of profit with significant downside risk. Monte Carlo strongly favors exiting positions."

    baseline_trajectory = [
        {"label": "Current", "year_offset": 0, "price": round(current_price, 2)},
        {"label": "3M", "year_offset": 0.25, "price": baseline_3mo["base"]},
        {"label": "6M", "year_offset": 0.5, "price": baseline_6mo["base"]},
        {"label": "1Y", "year_offset": 1, "price": baseline_1y["base"]},
        {"label": "2Y", "year_offset": 2, "price": baseline_2y["base"]},
    ]
    ai_adjusted_trajectory = [
        {"label": "Current", "year_offset": 0, "price": round(current_price, 2)},
        {"label": "3M", "year_offset": 0.25, "price": at_3mo["base"]},
        {"label": "6M", "year_offset": 0.5, "price": at_6mo["base"]},
        {"label": "1Y", "year_offset": 1, "price": at_1y["base"]},
        {"label": "2Y", "year_offset": 2, "price": at_2y["base"]},
    ]

    return {
        "symbol": symbol,
        "company_name": company_name,
        "current_price": round(current_price, 2),
        "forecast_horizon": "2 Years",
        "scenarios": {
            "3mo": at_3mo,
            "6mo": at_6mo,
            "1y": at_1y,
            "2y": at_2y,
        },
        "baseline_scenarios": {
            "3mo": baseline_3mo,
            "6mo": baseline_6mo,
            "1y": baseline_1y,
            "2y": baseline_2y,
        },
        "baseline_trajectory": baseline_trajectory,
        "ai_adjusted_trajectory": ai_adjusted_trajectory,
        "probability": {
            "profit": round(prob_profit, 1),
            "gain_20pct": round(prob_20_up, 1),
            "loss_20pct": round(prob_20_down, 1),
        },
        "metrics": {
            "expected_return_2y": round(expected_return, 1),
            "annualized_vol": round(sigma_annual * 100, 1),
            "sharpe_ratio": round(mu_annual / sigma_annual, 2) if sigma_annual > 0 else 0,
            "return_1y": round(float(ret_1y), 1),
            "mcs_score": round(float(raw_score), 2),
            "mcs_discount_factor": round(float(discount_factor), 3),
            "baseline_growth_pct": round(float(mcs_adjustment["baseline_growth_pct"]), 2),
            "ai_adjusted_growth_pct": round(float(mcs_adjustment["ai_adjusted_growth_pct"]), 2),
        },
        "trend": {
            "sma_50": round(sma_50, 2),
            "sma_200": round(sma_200, 2),
            "above_sma50": above_sma50,
            "above_sma200": above_sma200,
            "golden_cross": golden_cross,
        },
        "confidence_cone": cone,
        "verdict": verdict,
        "verdict_text": verdict_text,
        "n_simulations": n_sims,
    }
