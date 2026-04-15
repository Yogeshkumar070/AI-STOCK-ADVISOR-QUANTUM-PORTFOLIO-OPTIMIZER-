from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
from typing import Any

import yfinance as yf
from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from langchain_core.prompts import PromptTemplate
except ImportError:
    from langchain.prompts import PromptTemplate

try:
    from backend.data.vector_db import collection, seed_test_data as seed_vector_test_data
except ModuleNotFoundError:
    from data.vector_db import collection, seed_test_data as seed_vector_test_data


PROMPT = PromptTemplate.from_template(
    """
You are an expert quantitative financial auditor. Analyze the following earnings call transcripts for {ticker}.
Extract ANY forward-looking financial targets, guidance, or projections.

CRITICAL PROXY MAPPING RULES:
Because our verification engine relies on standardized accounting APIs, you MUST translate management's industry-specific jargon into one of these EXACT keys: 'Total Revenue', 'Operating Income', or 'Net Income'.

- If management discusses "Loan Growth", "Advances Growth", "Credit Growth", "NII", or "Top-line", you MUST map the metric to: "Total Revenue".
- If management discusses "Profits", "PAT", "Bottom-line", or "Earnings", map it to: "Net Income".
- If management discusses "EBITDA", "Core Operating Profit", or "Margins", map it to: "Operating Income".

Do NOT extract targets for highly specific ratios (like Cost-to-Income or NPA) as they cannot be verified.

Convert relative time ("next year", "FY22") into an absolute target year. Assume the text is from the 'year_made'.

Output ONLY a valid JSON array of objects.
Format: [{{"year_made": 2020, "target_year": 2021, "metric": "Total Revenue", "promised_growth_pct": 15.0, "quote": "We expect our loan book to grow by 15 percent..."}}]

Transcripts: {text}
""".strip()
)

METRIC_MAP = {
    "totalrevenue": "Total Revenue",
    "revenue": "Total Revenue",
    "sales": "Total Revenue",
    "operatingincome": "Operating Income",
    "operatingmargin": "Operating Income",
    "operatingmargins": "Operating Income",
    "operatingprofit": "Operating Income",
    "ebit": "Operating Income",
    "netincome": "Net Income",
    "profit": "Net Income",
    "pat": "Net Income",
    "basiceps": "Basic EPS",
    "dilutedeps": "Diluted EPS",
    "eps": "Basic EPS",
}

AUDIT_CATEGORY_MAP = {
    "Total Revenue": "Revenue",
    "Operating Income": "Profit",
    "Net Income": "Profit",
    "Basic EPS": "Profit",
    "Diluted EPS": "Profit",
}

BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = BASE_DIR / "cache" / "mcs_audits"
GUIDANCE_DIR = BASE_DIR / "data" / "management_guidance"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_llm() -> ChatGoogleGenerativeAI | None:
    if not os.getenv("GOOGLE_API_KEY"):
        return None
    try:
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    except Exception:
        return None


def _normalize_metric(raw_metric: str | None) -> str | None:
    if not raw_metric:
        return None
    cleaned = re.sub(r"[^a-z]", "", raw_metric.lower())
    return METRIC_MAP.get(cleaned)


def _parse_years(text: str, fallback_year: int | None) -> tuple[int | None, int | None]:
    years = [int(match) for match in re.findall(r"\b(20\d{2})\b", text)]
    if len(years) >= 2:
        return years[0], years[1]
    if len(years) == 1:
        target_year = years[0]
        return fallback_year or (target_year - 1), target_year
    if fallback_year:
        return fallback_year, fallback_year + 1
    return None, None


def _heuristic_extract(documents: list[str], metadatas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    promises = []
    for document, metadata in zip(documents, metadatas):
        growth_match = re.search(r"(\d+(?:\.\d+)?)\s*%", document)
        if not growth_match:
            continue

        year_made, target_year = _parse_years(document, metadata.get("year"))
        if target_year is None:
            continue

        metric = None
        lower = document.lower()
        for needle, standardized in METRIC_MAP.items():
            if needle in re.sub(r"[^a-z]", "", lower):
                metric = standardized
                break
        if metric is None:
            metric = "Total Revenue"

        promises.append(
            {
                "year_made": year_made or target_year - 1,
                "target_year": target_year,
                "metric": metric,
                "promised_growth_pct": float(growth_match.group(1)),
                "quote": document.strip(),
            }
        )
    return promises


def extract_promises(ticker: str) -> list[dict[str, Any]]:
    """Retrieve transcript context from Chroma and extract structured promises."""
    normalized = ticker.upper().replace(".NS", "")
    results = collection.get(where={"ticker": normalized}, include=["documents", "metadatas"])
    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []

    if not documents:
        return []

    combined_text = " ".join(documents)
    llm = _get_llm()
    if llm is not None:
        try:
            response = llm.invoke(PROMPT.format(ticker=normalized, text=combined_text))

            print(f"\n[DEBUG] Gemini Raw Response:\n{response.content}\n")

            clean_json = response.content.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            normalized_promises = []
            for item in parsed:
                metric = _normalize_metric(item.get("metric")) or item.get("metric")
                normalized_promises.append(
                    {
                        "year_made": int(item.get("year_made")),
                        "target_year": int(item.get("target_year")),
                        "metric": metric,
                        "promised_growth_pct": float(item.get("promised_growth_pct")),
                        "quote": item.get("quote", ""),
                    }
                )
            if normalized_promises:
                print(f"SUCCESS: Gemini extracted {len(normalized_promises)} promises.")
                return normalized_promises
        except Exception as e:
            print(f"CRITICAL GEMINI ERROR: {str(e)}")
            return []

    return _heuristic_extract(documents, metadatas)


def _fetch_financials(ticker: str):
    stock = yf.Ticker(f"{ticker}.NS" if not ticker.endswith(".NS") else ticker)
    for attr_name in ("financials", "income_stmt", "quarterly_income_stmt"):
        try:
            frame = getattr(stock, attr_name)
            if frame is not None and not frame.empty:
                return frame.T
        except Exception:
            continue
    return None


def _cache_path(ticker: str) -> Path:
    return CACHE_DIR / f"{ticker.upper().replace('.NS', '')}.json"


def _load_cached_audit(ticker: str) -> dict[str, Any] | None:
    path = _cache_path(ticker)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if (
            isinstance(payload, dict)
            and payload.get("chart_series", {}).get("revenue")
            and payload.get("chart_series", {}).get("profit")
            and payload.get("projection", {}).get("revenue")
            and payload.get("projection", {}).get("profit")
        ):
            return payload
        return None
    except Exception:
        return None


def _save_cached_audit(ticker: str, payload: dict[str, Any]) -> None:
    path = _cache_path(ticker)
    serializable = dict(payload)
    serializable["cache"] = {
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "path": str(path),
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(serializable, handle, indent=2)


def _load_guidance_seed(ticker: str) -> list[dict[str, Any]]:
    path = GUIDANCE_DIR / f"{ticker.upper().replace('.NS', '')}.json"
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload.get("history", [])
    except Exception:
        return []


def _normalize_financials(financials):
    if financials is None or financials.empty:
        return None

    normalized = financials.copy()
    fiscal_years = []
    for idx in normalized.index:
        match = re.search(r"(20\d{2})", str(idx))
        if hasattr(idx, "year"):
            fiscal_years.append(idx.year)
        elif match:
            fiscal_years.append(int(match.group(1)))
        else:
            fiscal_years.append(None)
    normalized["fiscal_year"] = fiscal_years

    if "fiscal_year" not in normalized.columns or normalized.empty:
        return None

    normalized = normalized.dropna(subset=["fiscal_year"]).copy()
    normalized["fiscal_year"] = normalized["fiscal_year"].astype(int)
    normalized = normalized.sort_values("fiscal_year")
    normalized = normalized.drop_duplicates(subset=["fiscal_year"], keep="last")
    return normalized


def _annual_growth_series(financials, metric: str) -> list[dict[str, Any]]:
    if financials is None or financials.empty or metric not in financials.columns:
        return []

    rows = []
    metric_series = financials[["fiscal_year", metric]].dropna()
    for i in range(1, len(metric_series)):
        prev = metric_series.iloc[i - 1]
        current = metric_series.iloc[i]
        try:
            prev_value = float(prev[metric])
            current_value = float(current[metric])
        except (TypeError, ValueError):
            continue
        if prev_value <= 0:
            continue
        growth = ((current_value - prev_value) / prev_value) * 100
        rows.append(
            {
                "year": int(current["fiscal_year"]),
                "previous_year": int(prev["fiscal_year"]),
                "actual": round(growth, 2),
                "metric": metric,
            }
        )
    return rows


def _promise_category(metric: str | None) -> str | None:
    if not metric:
        return None
    return AUDIT_CATEGORY_MAP.get(metric)


def _aggregate_promises(promises: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = {}

    for promise in promises:
        metric = _normalize_metric(promise.get("metric")) or promise.get("metric")
        category = _promise_category(metric)
        if category is None:
            continue
        key = (int(promise["target_year"]), category)
        grouped.setdefault(key, []).append(promise)

    aggregated = {}
    for key, items in grouped.items():
        promised_values = [float(item["promised_growth_pct"]) for item in items]
        aggregated[key] = {
            "promised": round(sum(promised_values) / len(promised_values), 2),
            "quote": items[0].get("quote", ""),
            "metric": items[0].get("metric"),
            "source_year": int(items[0].get("year_made")),
        }
    return aggregated


def _aggregate_seed_guidance(seed_items: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, Any]]:
    aggregated = {}
    for item in seed_items:
        quarter = str(item.get("quarter", ""))
        year_match = re.search(r"(20\d{2})", quarter)
        base_year = int(year_match.group(1)) if year_match else None
        if base_year is None:
            continue
        target_year = base_year + 1
        metric_name = str(item.get("metric", "")).lower()
        category = "Profit" if "margin" in metric_name or "profit" in metric_name else "Revenue"
        actual_value = item.get("actual_value")
        try:
            promised = float(item.get("target_value")) if item.get("target_value") is not None else None
        except (TypeError, ValueError):
            promised = None

        if promised is None:
            statement = str(item.get("statement", "")).lower()
            growth_match = re.search(r"(\d+(?:\.\d+)?)\s*%", statement)
            if growth_match:
                promised = float(growth_match.group(1))

        if promised is None:
            if item.get("delivered") is True and actual_value is not None:
                promised = float(actual_value)
            elif item.get("delivered") is False and actual_value is not None:
                promised = abs(float(actual_value)) + 5

        if promised is None:
            continue

        aggregated[(target_year, category)] = {
            "promised": round(promised, 2),
            "quote": item.get("statement", ""),
            "metric": item.get("metric", category),
            "source_year": base_year,
            "source_type": "seed_guidance",
        }
    return aggregated


def _build_category_audits(promises: list[dict[str, Any]], financials) -> dict[str, list[dict[str, Any]]]:
    promise_lookup = _aggregate_promises(promises)
    seed_lookup = _aggregate_seed_guidance(_load_guidance_seed(promises[0]["quote"].split()[0] if False else ""))  # placeholder
    revenue_growth = _annual_growth_series(financials, "Total Revenue")
    profit_growth = _annual_growth_series(financials, "Net Income")

    category_actuals = {"Revenue": revenue_growth, "Profit": profit_growth}
    category_audits: dict[str, list[dict[str, Any]]] = {"Revenue": [], "Profit": []}

    for category, series in category_actuals.items():
        for item in series[-5:]:
            promise_info = promise_lookup.get((item["year"], category))
            promised = promise_info["promised"] if promise_info else None
            actual = item["actual"]
            if promised is None:
                hit_rate = None
            elif actual >= promised:
                hit_rate = 100.0
            elif actual <= 0 and promised > 0:
                hit_rate = 0.0
            else:
                hit_rate = max(0.0, min((actual / promised) * 100, 100.0))

            category_audits[category].append(
                {
                    "year": str(item["year"]),
                    "category": category,
                    "metric": item["metric"],
                    "promised": round(promised, 2) if promised is not None else None,
                    "actual": round(actual, 2),
                    "hit_rate": round(hit_rate, 2) if hit_rate is not None else None,
                    "quote": promise_info["quote"] if promise_info else "",
                    "source_year": promise_info["source_year"] if promise_info else None,
                }
            )

    return category_audits


def _build_category_audits_for_ticker(ticker: str, promises: list[dict[str, Any]], financials) -> dict[str, list[dict[str, Any]]]:
    promise_lookup = _aggregate_promises(promises)
    promise_lookup.update(_aggregate_seed_guidance(_load_guidance_seed(ticker)))

    revenue_growth = _annual_growth_series(financials, "Total Revenue")
    profit_growth = _annual_growth_series(financials, "Net Income")

    category_actuals = {"Revenue": revenue_growth, "Profit": profit_growth}
    category_audits: dict[str, list[dict[str, Any]]] = {"Revenue": [], "Profit": []}

    for category, series in category_actuals.items():
        last_five = series[-5:]
        previous_actuals = [row["actual"] for row in last_five]
        rolling_baseline = sum(previous_actuals) / len(previous_actuals) if previous_actuals else 10.0

        for index, item in enumerate(last_five):
            promise_info = promise_lookup.get((item["year"], category))
            promised = promise_info["promised"] if promise_info else None
            actual = item["actual"]
            if promised is None:
                prior_actuals = [row["actual"] for row in last_five[:index] if row["actual"] is not None]
                promised = round(sum(prior_actuals) / len(prior_actuals), 2) if prior_actuals else round(rolling_baseline, 2)
                source_type = "historical_proxy"
                quote = "Proxy promise generated from trailing delivered growth because no auditable statement was cached."
                source_year = item["previous_year"]
            else:
                source_type = promise_info.get("source_type", "transcript")
                quote = promise_info["quote"]
                source_year = promise_info["source_year"]

            if actual >= promised:
                hit_rate = 100.0
            elif actual <= 0 and promised > 0:
                hit_rate = 0.0
            else:
                hit_rate = max(0.0, min((actual / promised) * 100, 100.0))

            category_audits[category].append(
                {
                    "year": str(item["year"]),
                    "category": category,
                    "metric": item["metric"],
                    "promised": round(promised, 2),
                    "actual": round(actual, 2),
                    "hit_rate": round(hit_rate, 2),
                    "quote": quote,
                    "source_year": source_year,
                    "source_type": source_type,
                }
            )

    return category_audits


def _ensure_projection_year_labels(series: list[dict[str, Any]], projection: dict[str, Any]) -> list[dict[str, Any]]:
    output = list(series)
    if projection.get("target_year"):
        output.append(
            {
                "year": f"{projection['target_year']} (Proj)",
                "promised": projection["base_projection"],
                "actual": None,
                "aiAdjusted": projection["ai_adjusted"],
                "metric": "Prediction",
                "source_type": "projection",
            }
        )
    return output


def _predict_next_year(category_audits: list[dict[str, Any]], fallback_score: float, reported_through_year: int | None) -> dict[str, Any]:
    if not category_audits:
        base_projection = 12.0
        credibility_factor = fallback_score / 100
    else:
        recent_promises = [item["promised"] for item in category_audits if item["promised"] is not None][-3:]
        recent_actuals = [item["actual"] for item in category_audits][-3:]
        recent_hit_rates = [item["hit_rate"] for item in category_audits if item["hit_rate"] is not None][-3:]

        base_projection = (
            sum(recent_promises) / len(recent_promises)
            if recent_promises
            else sum(recent_actuals) / len(recent_actuals)
            if recent_actuals
            else 12.0
        )
        credibility_factor = (
            (sum(recent_hit_rates) / len(recent_hit_rates)) / 100
            if recent_hit_rates
            else fallback_score / 100
        )

    ai_adjusted = base_projection * credibility_factor
    base_year = (reported_through_year + 1) if reported_through_year else None
    target_year = (reported_through_year + 2) if reported_through_year else None

    return {
        "base_year": base_year,
        "target_year": target_year,
        "base_projection": round(base_projection, 2),
        "credibility_factor": round(credibility_factor * 100, 2),
        "ai_adjusted": round(ai_adjusted, 2),
    }


def _build_chart_series(category_audits: list[dict[str, Any]], projection: dict[str, Any]) -> list[dict[str, Any]]:
    series = [
        {
            "year": item["year"],
            "promised": item["promised"],
            "actual": item["actual"],
            "aiAdjusted": None,
            "metric": item["category"],
        }
        for item in category_audits
    ]

    if projection.get("target_year"):
        series.append(
            {
                "year": f"{projection['target_year']} (Proj)",
                "promised": projection["base_projection"],
                "actual": None,
                "aiAdjusted": projection["ai_adjusted"],
                "metric": "Prediction",
            }
        )

    return series


def _find_row_for_year(financials, year: int):
    return next((idx for idx in financials.index if str(year) in str(idx)), None)


def seed_test_data(ticker: str) -> bool:
    return seed_vector_test_data(ticker)


def calculate_mcs(ticker: str) -> dict[str, Any]:
    """Audit extracted promises against actual reported financial outcomes."""
    normalized = ticker.upper().replace(".NS", "")
    cached = _load_cached_audit(normalized)
    if cached:
        return cached

    promises = extract_promises(normalized)
    financials = _fetch_financials(normalized)
    if financials is None:
        fallback = {
            "ticker": normalized,
            "mcs_score": 50.0,
            "error": "Financial data unavailable.",
            "audits": [],
        }
        _save_cached_audit(normalized, fallback)
        return fallback

    financials = _normalize_financials(financials)
    if financials is None:
        fallback = {
            "ticker": normalized,
            "mcs_score": 50.0,
            "error": "Financial statements could not be normalized.",
            "audits": [],
        }
        _save_cached_audit(normalized, fallback)
        return fallback

    audit_results = []
    total_hit_rate = 0.0
    valid_audits = 0

    for promise in promises:
        target_year = int(promise["target_year"])
        year_made = int(promise["year_made"])
        metric = _normalize_metric(promise.get("metric")) or promise.get("metric")
        promised_growth = float(promise["promised_growth_pct"])

        actual_row = _find_row_for_year(financials, target_year)
        prev_row = _find_row_for_year(financials, year_made)

        if actual_row is None or prev_row is None or metric not in financials.columns:
            continue

        actual_now = financials.loc[actual_row, metric]
        actual_prev = financials.loc[prev_row, metric]

        try:
            actual_now = float(actual_now)
            actual_prev = float(actual_prev)
        except (TypeError, ValueError):
            continue

        if actual_prev <= 0:
            continue

        actual_growth = ((actual_now - actual_prev) / actual_prev) * 100

        if actual_growth >= promised_growth:
            hit_rate = 100.0
        elif actual_growth <= 0 and promised_growth > 0:
            hit_rate = 0.0
        else:
            hit_rate = max(0.0, min((actual_growth / promised_growth) * 100, 100.0))

        total_hit_rate += hit_rate
        valid_audits += 1
        category = _promise_category(metric) or "Revenue"
        audit_results.append(
            {
                "year": str(target_year),
                "category": category,
                "metric": metric,
                "promised": round(promised_growth, 2),
                "actual": round(actual_growth, 2),
                "hit_rate": round(hit_rate, 2),
                "quote": promise.get("quote", ""),
            }
        )

    final_mcs = round(total_hit_rate / valid_audits, 2) if valid_audits > 0 else 50.0
    annual_audits = _build_category_audits_for_ticker(normalized, promises, financials)
    last_year = int(financials["fiscal_year"].max()) if not financials.empty else None
    revenue_projection = _predict_next_year(annual_audits["Revenue"], final_mcs, last_year)
    profit_projection = _predict_next_year(annual_audits["Profit"], final_mcs, last_year)

    payload = {
        "ticker": normalized,
        "mcs_score": final_mcs,
        "audits": audit_results,
        "annual_audits": annual_audits,
        "chart_series": {
            "revenue": _ensure_projection_year_labels(_build_chart_series(annual_audits["Revenue"], {"target_year": None, "base_projection": None, "ai_adjusted": None}), revenue_projection),
            "profit": _ensure_projection_year_labels(_build_chart_series(annual_audits["Profit"], {"target_year": None, "base_projection": None, "ai_adjusted": None}), profit_projection),
        },
        "projection": {
            "reported_through_year": last_year,
            "revenue": revenue_projection,
            "profit": profit_projection,
        },
        "details": "Audited against historical financial statements and cached locally for reuse." if audit_results else "Built from historical financial statements and cached locally for reuse.",
        "storage": {
            "cache_key": normalized,
            "cache_path": str(_cache_path(normalized)),
        },
    }
    _save_cached_audit(normalized, payload)
    return payload
