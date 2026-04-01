"""
Bull vs Bear AI Debate Engine
Two Claude personas debate a stock from opposing sides,
producing structured arguments, rebuttals, and a moderator verdict.
"""

import os
import json
import yfinance as yf
import anthropic
from typing import Dict, Any


def _get_debate_data(symbol: str) -> Dict[str, Any]:
    """Gather comprehensive fundamentals for the debate."""
    ticker_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    # 1-year price performance
    price_change_1y = None
    try:
        hist = ticker.history(period="1y")
        if not hist.empty:
            start = float(hist["Close"].iloc[0])
            end = float(hist["Close"].iloc[-1])
            price_change_1y = round(((end - start) / start) * 100, 2)
    except Exception:
        pass

    # Quarterly EPS trend (last 4 quarters)
    eps_trend = []
    try:
        eh = ticker.earnings_history
        if eh is not None and not eh.empty:
            for idx, row in eh.tail(4).iterrows():
                eps_trend.append({
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                    "eps_actual": float(row["epsActual"]) if row.get("epsActual") is not None else None,
                    "surprise_pct": float(row["surprisePercent"]) if row.get("surprisePercent") is not None else None,
                })
    except Exception:
        pass

    return {
        "company_name": info.get("longName") or info.get("shortName") or symbol,
        "symbol": symbol,
        "sector": info.get("sector", "Unknown"),
        "industry": info.get("industry", "Unknown"),
        "current_price": info.get("currentPrice"),
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow"),
        "price_change_1y_pct": price_change_1y,
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "price_to_book": info.get("priceToBook"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "total_revenue": info.get("totalRevenue"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "profit_margins": info.get("profitMargins"),
        "operating_margins": info.get("operatingMargins"),
        "free_cash_flow": info.get("freeCashflow"),
        "total_cash": info.get("totalCash"),
        "total_debt": info.get("totalDebt"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "short_ratio": info.get("shortRatio"),
        "recommendation_key": info.get("recommendationKey"),
        "recommendation_mean": info.get("recommendationMean"),
        "target_mean_price": info.get("targetMeanPrice"),
        "target_high_price": info.get("targetHighPrice"),
        "target_low_price": info.get("targetLowPrice"),
        "eps_trend": eps_trend,
        "business_summary": (info.get("longBusinessSummary") or "")[:600],
        "employees": info.get("fullTimeEmployees"),
    }


def run_bull_bear_debate(symbol: str) -> Dict[str, Any]:
    """
    Runs a structured bull-bear debate using Claude as both analyst personas.
    Returns JSON with opening arguments, rebuttals, and moderator verdict.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set.")

    client = anthropic.Anthropic(api_key=api_key)
    data = _get_debate_data(symbol)

    prompt = f"""You are the moderator of a high-stakes institutional investment debate at a tier-1 hedge fund.
Two of the firm's top analysts are debating whether to BUY or SELL {data['company_name']} ({symbol}).

## STOCK DATA (NSE-listed Indian company)
{json.dumps(data, indent=2, default=str)}

## DEBATE RULES
- **BULL ANALYST**: Argues this is a strong BUY with material upside. Must cite specific numbers from the data.
- **BEAR ANALYST**: Argues this should be SOLD or AVOIDED with real downside risk. Must cite specific numbers from the data.
- Each analyst gives 3 distinct arguments backed by data.
- Each analyst gives a rebuttal to the other's strongest point.
- You (moderator) give a final verdict based purely on the weight of evidence.

Arguments must be sharp, institutional-grade, and cite REAL figures from the data above.
Avoid generic statements — every claim must reference a specific metric or data point.

Respond ONLY with valid JSON — no markdown, no text outside the JSON:
{{
    "company_name": "{data['company_name']}",
    "symbol": "{symbol}",
    "current_price": {data.get('current_price') or 0},
    "debate_title": "<one punchy line summarizing the core tension in this debate>",
    "bull_opening": {{
        "headline": "<1-sentence bold bull thesis>",
        "argument_1": {{
            "point": "<argument title — 4-6 words>",
            "detail": "<2-3 sentences citing specific data points>"
        }},
        "argument_2": {{
            "point": "<argument title — 4-6 words>",
            "detail": "<2-3 sentences citing specific data points>"
        }},
        "argument_3": {{
            "point": "<argument title — 4-6 words>",
            "detail": "<2-3 sentences citing specific data points>"
        }},
        "price_target": "<12-month bull price target with currency symbol>",
        "upside_pct": <integer percentage upside from current price>,
        "confidence": <integer 0-100>
    }},
    "bear_opening": {{
        "headline": "<1-sentence bold bear thesis>",
        "argument_1": {{
            "point": "<argument title — 4-6 words>",
            "detail": "<2-3 sentences citing specific data points>"
        }},
        "argument_2": {{
            "point": "<argument title — 4-6 words>",
            "detail": "<2-3 sentences citing specific data points>"
        }},
        "argument_3": {{
            "point": "<argument title — 4-6 words>",
            "detail": "<2-3 sentences citing specific data points>"
        }},
        "price_target": "<12-month bear price target with currency symbol>",
        "downside_pct": <integer percentage downside from current price>,
        "confidence": <integer 0-100>
    }},
    "bull_rebuttal": "<2-3 sentences: Bull directly counters the Bear's single strongest argument>",
    "bear_rebuttal": "<2-3 sentences: Bear directly counters the Bull's single strongest argument>",
    "moderator_verdict": {{
        "winner": "<BULL|BEAR|DRAW>",
        "margin": "<DECISIVE|NARROW|SLIGHT>",
        "net_conviction": <integer -100 to +100, positive = bullish, 0 = perfectly neutral>,
        "key_deciding_factor": "<the one data point or factor that tips the verdict>",
        "verdict_summary": "<3-4 sentences of balanced, evidence-based final analysis>",
        "suggested_action": "<STRONG BUY|BUY|ACCUMULATE|HOLD|REDUCE|SELL|STRONG SELL>",
        "risk_level": "<LOW|MODERATE|HIGH|VERY HIGH>"
    }}
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
