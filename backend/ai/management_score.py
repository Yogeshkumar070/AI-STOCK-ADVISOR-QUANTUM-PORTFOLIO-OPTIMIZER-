"""
Management Credibility Score Engine
Analyzes how consistently management delivers on expectations
using earnings surprises, revenue trends, and financial discipline.
"""

import os
import json
import yfinance as yf
import anthropic
from typing import Dict, Any


def _get_management_data(symbol: str) -> Dict[str, Any]:
    """Gather all data from yfinance needed for MCS analysis."""
    ticker_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    # --- Earnings History: EPS actual vs estimate ---
    earnings_data = []
    try:
        eh = ticker.earnings_history
        if eh is not None and not eh.empty:
            for idx, row in eh.iterrows():
                earnings_data.append({
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                    "eps_actual": float(row["epsActual"]) if row.get("epsActual") is not None else None,
                    "eps_estimate": float(row["epsEstimate"]) if row.get("epsEstimate") is not None else None,
                    "surprise_pct": float(row["surprisePercent"]) if row.get("surprisePercent") is not None else None,
                })
    except Exception:
        pass

    # --- Quarterly Revenue Trend ---
    quarterly_revenue = []
    try:
        qs = ticker.quarterly_income_stmt
        if qs is not None and not qs.empty and "Total Revenue" in qs.index:
            rev = qs.loc["Total Revenue"]
            for col in list(rev.index)[:8]:
                val = rev[col]
                quarterly_revenue.append({
                    "period": str(col.date()) if hasattr(col, "date") else str(col),
                    "revenue": float(val) if val is not None else None,
                })
    except Exception:
        pass

    # --- Analyst Recommendations ---
    analyst_recs = []
    try:
        recs = ticker.recommendations
        if recs is not None and not recs.empty:
            for idx, row in recs.tail(10).iterrows():
                analyst_recs.append({
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                    "firm": row.get("Firm", "Unknown"),
                    "to_grade": row.get("To Grade", ""),
                    "action": row.get("Action", ""),
                })
    except Exception:
        pass

    return {
        "company_name": info.get("longName") or info.get("shortName") or symbol,
        "sector": info.get("sector", "Unknown"),
        "industry": info.get("industry", "Unknown"),
        "earnings_data": earnings_data,
        "quarterly_revenue": quarterly_revenue,
        "analyst_recommendations": analyst_recs,
        "current_price": info.get("currentPrice"),
        "target_mean_price": info.get("targetMeanPrice"),
        "target_high_price": info.get("targetHighPrice"),
        "target_low_price": info.get("targetLowPrice"),
        "recommendation_key": info.get("recommendationKey"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "profit_margins": info.get("profitMargins"),
        "operating_margins": info.get("operatingMargins"),
    }


def calculate_management_score(symbol: str) -> Dict[str, Any]:
    """
    Uses Claude to analyze management delivery track record and return
    a structured credibility score with factor breakdown.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set.")

    client = anthropic.Anthropic(api_key=api_key)
    data = _get_management_data(symbol)

    prompt = f"""You are a senior equity analyst at an institutional investment firm specializing in management quality assessment for Indian NSE-listed companies.

Analyze the following data for {data['company_name']} ({symbol}) and produce a Management Credibility Score.

## Company Profile
- Sector: {data['sector']}
- Industry: {data['industry']}
- Current Price: {data['current_price']}
- Analyst Target (Mean): {data['target_mean_price']}
- Analyst Target Range: {data['target_low_price']} – {data['target_high_price']}
- Recommendation: {data['recommendation_key']}

## Key Financial Metrics
- Trailing PE: {data['pe_ratio']}
- Forward PE: {data['forward_pe']}
- ROE: {data['roe']}
- Debt/Equity: {data['debt_to_equity']}
- Revenue Growth (YoY): {data['revenue_growth']}
- Earnings Growth (YoY): {data['earnings_growth']}
- Profit Margins: {data['profit_margins']}
- Operating Margins: {data['operating_margins']}

## Earnings History (EPS Actual vs Estimate — last 8 quarters)
{json.dumps(data['earnings_data'], indent=2)}

## Quarterly Revenue Trend (last 8 quarters)
{json.dumps(data['quarterly_revenue'], indent=2)}

## Recent Analyst Recommendations
{json.dumps(data['analyst_recommendations'], indent=2)}

## Scoring Task
Calculate a Management Credibility Score (0–100) across four weighted factors:
1. **Earnings Delivery** (30% weight): Consistency of beating/meeting EPS estimates. Calculate actual beat rate from earnings_data.
2. **Revenue Consistency** (25% weight): Stability and growth direction of quarterly revenues.
3. **Financial Discipline** (25% weight): Quality of ROE, margins, debt management.
4. **Analyst Confidence** (20% weight): Strength of analyst consensus, price target vs current price.

Respond ONLY with valid JSON — no markdown, no explanation outside the JSON:
{{
    "score": <integer 0-100>,
    "verdict": "<EXCELLENT|STRONG|MODERATE|WEAK|POOR>",
    "earnings_delivery_score": <integer 0-100>,
    "revenue_consistency_score": <integer 0-100>,
    "financial_discipline_score": <integer 0-100>,
    "analyst_confidence_score": <integer 0-100>,
    "beat_rate": "<e.g. 5 out of 7 quarters beat estimates>",
    "avg_surprise_pct": "<e.g. +3.8% average earnings surprise>",
    "key_strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "key_concerns": ["<concern 1>", "<concern 2>", "<concern 3>"],
    "credibility_summary": "<2-3 sentence evidence-based analysis of management track record>",
    "trend": "<IMPROVING|STABLE|DETERIORATING>",
    "investor_note": "<1 specific, actionable insight for an investor today>"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    result = json.loads(raw)
    # Attach raw earnings data for the frontend chart
    result["earnings_history"] = data["earnings_data"][:8]
    result["current_price"] = data["current_price"]
    result["target_mean_price"] = data["target_mean_price"]
    result["company_name"] = data["company_name"]
    return result
