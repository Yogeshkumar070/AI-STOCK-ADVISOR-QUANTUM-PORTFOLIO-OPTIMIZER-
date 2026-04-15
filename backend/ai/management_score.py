"""
Management Credibility Score (MCS) — Pure Algorithmic Engine
No API key required. Uses only yfinance data.

Scores management's promise-vs-delivery track record by analyzing:
- Quarterly earnings surprises (EPS actual vs estimate)
- Revenue growth consistency across quarters
- Financial discipline (ROE, margins, debt management)
- Analyst confidence (consensus rating + target price upside)
"""

import yfinance as yf
import numpy as np
from typing import Dict, Any, List


def _safe(val, default=None):
    """Safely extract a value, returning default for None/NaN."""
    if val is None:
        return default
    try:
        if isinstance(val, float) and np.isnan(val):
            return default
    except (TypeError, ValueError):
        pass
    return val


def _get_data(symbol: str) -> Dict[str, Any]:
    """Gather all data needed for MCS from yfinance."""
    ts = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
    tk = yf.Ticker(ts)
    info = tk.info

    # ── Earnings History ──
    earnings = []
    try:
        eh = tk.earnings_history
        if eh is not None and not eh.empty:
            for idx, row in eh.iterrows():
                earnings.append({
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                    "eps_actual": _safe(row.get("epsActual")),
                    "eps_estimate": _safe(row.get("epsEstimate")),
                    "surprise_pct": _safe(row.get("surprisePercent")),
                })
    except Exception:
        pass

    # ── Quarterly Revenue ──
    q_rev = []
    try:
        qs = tk.quarterly_income_stmt
        if qs is not None and not qs.empty and "Total Revenue" in qs.index:
            rev = qs.loc["Total Revenue"]
            for col in list(rev.index)[:8]:
                v = rev[col]
                q_rev.append({
                    "period": str(col.date()) if hasattr(col, "date") else str(col),
                    "revenue": float(v) if v is not None and not (isinstance(v, float) and np.isnan(v)) else None,
                })
    except Exception:
        pass

    # ── Quarterly Net Income ──
    q_income = []
    try:
        qs = tk.quarterly_income_stmt
        if qs is not None and not qs.empty and "Net Income" in qs.index:
            ni = qs.loc["Net Income"]
            for col in list(ni.index)[:8]:
                v = ni[col]
                q_income.append({
                    "period": str(col.date()) if hasattr(col, "date") else str(col),
                    "net_income": float(v) if v is not None and not (isinstance(v, float) and np.isnan(v)) else None,
                })
    except Exception:
        pass

    return {
        "company_name": info.get("longName") or info.get("shortName") or symbol,
        "sector": info.get("sector", "Unknown"),
        "industry": info.get("industry", "Unknown"),
        "earnings": earnings,
        "quarterly_revenue": q_rev,
        "quarterly_income": q_income,
        "pe": _safe(info.get("trailingPE")),
        "forward_pe": _safe(info.get("forwardPE")),
        "roe": _safe(info.get("returnOnEquity")),
        "de": _safe(info.get("debtToEquity")),
        "rev_growth": _safe(info.get("revenueGrowth")),
        "earn_growth": _safe(info.get("earningsGrowth")),
        "profit_margins": _safe(info.get("profitMargins")),
        "op_margins": _safe(info.get("operatingMargins")),
        "gross_margins": _safe(info.get("grossMargins")),
        "rec_key": info.get("recommendationKey"),
        "rec_mean": _safe(info.get("recommendationMean")),
        "current_price": _safe(info.get("currentPrice")),
        "target_mean": _safe(info.get("targetMeanPrice")),
        "target_high": _safe(info.get("targetHighPrice")),
        "target_low": _safe(info.get("targetLowPrice")),
        "book_value": _safe(info.get("bookValue")),
        "eps": _safe(info.get("trailingEps")),
        "forward_eps": _safe(info.get("forwardEps")),
        "payout_ratio": _safe(info.get("payoutRatio")),
        "fcf": _safe(info.get("freeCashflow")),
        "revenue": _safe(info.get("totalRevenue")),
    }


# ═══════════════════════════════════════════════════════════════════
# SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _score_earnings(earnings: List[dict]) -> tuple:
    valid = [e for e in earnings if e["surprise_pct"] is not None]
    if not valid:
        return 50, "N/A", "0.0%", []

    beats = sum(1 for e in valid if e["surprise_pct"] > 0)
    meets = sum(1 for e in valid if abs(e["surprise_pct"]) <= 1)
    total = len(valid)
    beat_rate = beats / total
    avg_surprise = float(np.mean([e["surprise_pct"] for e in valid]))

    score = int(beat_rate * 70 + min(max(avg_surprise * 3, -30), 30))
    score = max(0, min(100, score))

    # Promise vs delivery timeline
    timeline = []
    for e in valid[:8]:
        status = "BEAT" if e["surprise_pct"] > 1 else ("MET" if abs(e["surprise_pct"]) <= 1 else "MISSED")
        timeline.append({
            "date": e["date"],
            "eps_actual": e["eps_actual"],
            "eps_estimate": e["eps_estimate"],
            "surprise_pct": round(e["surprise_pct"], 2),
            "status": status,
        })

    return score, f"{beats} out of {total} quarters beat estimates", f"{avg_surprise:+.1f}%", timeline


def _score_revenue(q_rev: List[dict]) -> tuple:
    valid = [q for q in q_rev if q["revenue"] is not None]
    if len(valid) < 2:
        return 50, []

    revs = list(reversed([q["revenue"] for q in valid]))
    periods = list(reversed([q["period"] for q in valid]))

    growth_q = sum(1 for i in range(1, len(revs)) if revs[i] > revs[i - 1])
    growth_rate = growth_q / (len(revs) - 1)
    total_growth = (revs[-1] - revs[0]) / abs(revs[0]) if revs[0] != 0 else 0

    score = int(growth_rate * 60 + min(max(total_growth * 100, -40), 40))
    score = max(0, min(100, score))

    # Revenue trend data for chart
    trend = []
    for i, r in enumerate(revs):
        trend.append({
            "period": periods[i],
            "revenue": round(r / 1e7, 2),  # in Crores
            "growth_qoq": round(((revs[i] - revs[i-1]) / abs(revs[i-1])) * 100, 1) if i > 0 and revs[i-1] != 0 else 0,
        })

    return score, trend


def _score_discipline(data: dict) -> int:
    scores = []

    roe = data["roe"]
    if roe is not None:
        if roe >= 0.20: scores.append(95)
        elif roe >= 0.15: scores.append(78)
        elif roe >= 0.10: scores.append(60)
        elif roe >= 0.05: scores.append(40)
        else: scores.append(20)

    pm = data["profit_margins"]
    if pm is not None:
        if pm >= 0.20: scores.append(92)
        elif pm >= 0.12: scores.append(72)
        elif pm >= 0.05: scores.append(50)
        else: scores.append(25)

    de = data["de"]
    if de is not None:
        if de <= 20: scores.append(95)
        elif de <= 50: scores.append(80)
        elif de <= 100: scores.append(55)
        elif de <= 150: scores.append(35)
        else: scores.append(15)

    om = data["op_margins"]
    if om is not None:
        if om >= 0.25: scores.append(90)
        elif om >= 0.15: scores.append(72)
        elif om >= 0.08: scores.append(50)
        else: scores.append(28)

    return int(np.mean(scores)) if scores else 50


def _score_analyst(data: dict) -> int:
    scores = []

    rm = data["rec_mean"]
    if rm is not None:
        scores.append(max(0, min(100, int((5 - rm) / 4 * 100))))

    cp = data["current_price"]
    tp = data["target_mean"]
    if cp and tp and cp > 0:
        upside = (tp - cp) / cp
        scores.append(max(0, min(100, int(50 + upside * 200))))

    return int(np.mean(scores)) if scores else 50


def _gen_strengths(data: dict, ed: int, rc: int, fd: int, ac: int) -> List[str]:
    pool = []
    roe = data["roe"]; pm = data["profit_margins"]; de = data["de"]
    rg = data["rev_growth"]; eg = data["earn_growth"]; fcf = data["fcf"]

    if ed >= 70: pool.append("Consistently beats earnings estimates — strong execution discipline")
    if rc >= 70: pool.append("Steady revenue growth demonstrates durable demand and market leadership")
    if roe is not None and roe >= 0.15: pool.append(f"ROE of {roe*100:.1f}% reflects excellent capital allocation")
    if pm is not None and pm >= 0.15: pool.append(f"Healthy net margins at {pm*100:.1f}% indicate competitive moat")
    if de is not None and de <= 50: pool.append(f"Conservative leverage (D/E: {de:.0f}) provides downside protection")
    if rg is not None and rg > 0.10: pool.append(f"Revenue growing at {rg*100:.1f}% YoY — above market average")
    if eg is not None and eg > 0.10: pool.append(f"Earnings growth of {eg*100:.1f}% signals improving profitability")
    if fcf is not None and fcf > 0: pool.append("Positive free cash flow supports dividends and reinvestment")
    if ac >= 75: pool.append("Strong analyst consensus reflects institutional conviction")

    return pool[:4] if pool else ["Limited data to assess strengths — monitor future quarters"]


def _gen_concerns(data: dict, ed: int, rc: int, fd: int, ac: int) -> List[str]:
    pool = []
    roe = data["roe"]; pm = data["profit_margins"]; de = data["de"]
    pe = data["pe"]; rg = data["rev_growth"]; fcf = data["fcf"]

    if ed < 45: pool.append("Frequently misses earnings estimates — execution questions persist")
    if rc < 45: pool.append("Inconsistent revenue trajectory suggests demand instability")
    if roe is not None and roe < 0.08: pool.append(f"ROE of {roe*100:.1f}% is below the 10% institutional threshold")
    if pm is not None and pm < 0.06: pool.append(f"Thin margins at {pm*100:.1f}% leave minimal room for error")
    if de is not None and de > 120: pool.append(f"High leverage (D/E: {de:.0f}) increases financial fragility")
    if pe is not None and pe > 50: pool.append(f"P/E of {pe:.1f}x suggests stretched valuation")
    if rg is not None and rg < -0.02: pool.append(f"Revenue declining at {rg*100:.1f}% — structural headwinds")
    if fcf is not None and fcf < 0: pool.append("Negative free cash flow — company is burning cash")
    if ac < 40: pool.append("Weak analyst consensus — limited institutional interest")

    return pool[:4] if pool else ["No major concerns identified from current data"]


def _verdict(score: int) -> str:
    if score >= 80: return "EXCELLENT"
    if score >= 65: return "STRONG"
    if score >= 45: return "MODERATE"
    if score >= 25: return "WEAK"
    return "POOR"


def _trend(ed: int, rc: int, data: dict) -> str:
    eg = data["earn_growth"]; rg = data["rev_growth"]
    if eg is not None and rg is not None:
        if eg > 0.05 and rg > 0.05: return "IMPROVING"
        if eg < -0.05 or rg < -0.05: return "DETERIORATING"
    if ed >= 65 and rc >= 60: return "IMPROVING"
    if ed < 40 or rc < 40: return "DETERIORATING"
    return "STABLE"


def _summary(data: dict, score: int, verdict: str, beat_rate: str) -> str:
    name = data["company_name"]
    parts = [f"{name} receives a {verdict} management credibility score of {score}/100."]
    if beat_rate != "N/A":
        parts.append(f"The company has beaten earnings estimates in {beat_rate}, reflecting {'strong' if score >= 65 else 'mixed'} execution capability.")
    roe = data["roe"]; pm = data["profit_margins"]
    if roe is not None and pm is not None:
        parts.append(f"With ROE at {roe*100:.1f}% and profit margins of {pm*100:.1f}%, financial discipline is {'robust' if score >= 65 else 'an area for improvement'}.")
    return " ".join(parts)


def _investor_note(data: dict, score: int) -> str:
    cp = data["current_price"]; tp = data["target_mean"]
    if cp and tp:
        upside = ((tp - cp) / cp) * 100
        if score >= 70 and upside > 10:
            return f"Strong track record + {upside:.0f}% analyst upside to ₹{tp:,.0f}. Accumulate on dips."
        if score >= 70:
            return f"Excellent management quality. Analyst target ₹{tp:,.0f} ({upside:+.0f}%). Hold for long-term compounding."
        if score < 45:
            return f"Weak management track record. Despite target of ₹{tp:,.0f}, execution risk is elevated — wait for improvement."
    if score >= 65:
        return "Solid management delivery. Monitor quarterly results to confirm sustained momentum."
    return "Management consistency needs improvement. Wait for 2-3 quarters of better execution before adding."


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def calculate_management_score(symbol: str) -> Dict[str, Any]:
    """Calculate complete MCS with factor breakdown, timeline, and insights."""
    data = _get_data(symbol)

    ed, beat_rate, avg_surprise, timeline = _score_earnings(data["earnings"])
    rc, rev_trend = _score_revenue(data["quarterly_revenue"])
    fd = _score_discipline(data)
    ac = _score_analyst(data)

    overall = int(ed * 0.30 + rc * 0.25 + fd * 0.25 + ac * 0.20)
    v = _verdict(overall)
    t = _trend(ed, rc, data)

    return {
        "score": overall,
        "verdict": v,
        "earnings_delivery_score": ed,
        "revenue_consistency_score": rc,
        "financial_discipline_score": fd,
        "analyst_confidence_score": ac,
        "beat_rate": beat_rate,
        "avg_surprise_pct": avg_surprise,
        "key_strengths": _gen_strengths(data, ed, rc, fd, ac),
        "key_concerns": _gen_concerns(data, ed, rc, fd, ac),
        "credibility_summary": _summary(data, overall, v, beat_rate),
        "trend": t,
        "investor_note": _investor_note(data, overall),
        "earnings_timeline": timeline,
        "revenue_trend": rev_trend,
        "current_price": data["current_price"],
        "target_mean_price": data["target_mean"],
        "company_name": data["company_name"],
        "sector": data["sector"],
        "industry": data["industry"],
        # Financial snapshot for display
        "snapshot": {
            "pe": data["pe"],
            "roe": round(data["roe"] * 100, 1) if data["roe"] else None,
            "de": round(data["de"], 1) if data["de"] else None,
            "profit_margins": round(data["profit_margins"] * 100, 1) if data["profit_margins"] else None,
            "rev_growth": round(data["rev_growth"] * 100, 1) if data["rev_growth"] else None,
            "earn_growth": round(data["earn_growth"] * 100, 1) if data["earn_growth"] else None,
            "eps": data["eps"],
            "forward_eps": data["forward_eps"],
        },
    }
