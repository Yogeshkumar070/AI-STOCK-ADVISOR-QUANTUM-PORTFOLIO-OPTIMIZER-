from fastapi import APIRouter, HTTPException
import yfinance as yf
import pandas as pd
from backend.data.cache_db import get_cached_mcs, save_mcs_to_cache
from backend.nlp.mcs_engine import calculate_mcs, seed_test_data

router = APIRouter()

TICKER_TAPE_LIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFY.NS", "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS",
    "TITAN.NS", "BAJFINANCE.NS", "WIPRO.NS", "HCLTECH.NS", "ADANIENT.NS",
    "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "COALINDIA.NS", "BAJAJFINSV.NS",
]

# ── STOCK OVERVIEW ──
@router.get("/overview/{symbol}")
def stock_overview(symbol: str):
    try:
        ticker_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
        ticker = yf.Ticker(ticker_symbol)
        history = ticker.history(period="1y")

        if history.empty:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found or delisted.")

        info = ticker.info

        ceo_name = "N/A"
        officers = info.get("companyOfficers", [])
        if officers and len(officers) > 0:
            ceo_name = officers[0].get("name", "N/A")

        return {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "long_business_summary": info.get("longBusinessSummary"),
            "website": info.get("website"),
            "city": info.get("city"),
            "fullTimeEmployees": info.get("fullTimeEmployees"),
            "ceo": ceo_name,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "revenue": info.get("totalRevenue"),
            "eps": info.get("trailingEps"),
            "dividend_yield": info.get("dividendYield"),
            "price_history": [
                {"Date": str(date.date()), "Close": round(row["Close"], 2)}
                for date, row in history.iterrows()
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching stock data")


# ── STOCK PRICES (FOR CHARTS) ──
@router.get("/prices/{symbol}")
def stock_prices(symbol: str, period: str = "1y"):
    try:
        ticker_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            raise HTTPException(status_code=404, detail="No price data found")

        return {
            "symbol": symbol,
            "period": period,
            "prices": [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"]),
                }
                for idx, row in hist.iterrows()
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── MARKET INDICES ──
INDEX_LIST = [
    {"symbols": ["^NSEI"], "label": "NIFTY 50"},
    {"symbols": ["^NSEBANK"], "label": "BANK NIFTY"},
    {"symbols": ["NIFTY_FIN_SERVICE.NS"], "label": "FIN NIFTY"},
    {"symbols": ["^BSESN"], "label": "SENSEX"},
    {"symbols": ["NIFTY_MID_SELECT.NS", "^CNXMIDCAP", "NIFTYMIDCAP150.NS"], "label": "MIDCPNIFTY"},
]


def fetch_index_snapshot(symbols: list[str]):
    last_error = None
    for candidate in symbols:
        try:
            t = yf.Ticker(candidate)
            hist = t.history(period="5d")
            if hist.empty or len(hist) < 1:
                raise ValueError("No data")

            price = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
            chg = price - prev
            pct = (chg / prev) * 100 if prev != 0 else 0

            return {
                "sym": candidate,
                "price": round(price, 2),
                "chg": round(chg, 2),
                "pct": round(pct, 2),
            }
        except Exception as exc:
            last_error = exc

    raise last_error or ValueError("No data")

@router.get("/indices")
def get_indices():
    results = []
    for idx in INDEX_LIST:
        try:
            snapshot = fetch_index_snapshot(idx["symbols"])
            results.append({
                "sym": snapshot["sym"], "label": idx["label"],
                "price": snapshot["price"], "chg": snapshot["chg"], "pct": snapshot["pct"],
            })
        except Exception:
            results.append({
                "sym": idx["symbols"][0], "label": idx["label"],
                "price": None, "chg": None, "pct": None,
            })
    return results


@router.get("/ticker-tape")
def ticker_tape():
    try:
        data = yf.download(TICKER_TAPE_LIST, period="5d", progress=False, auto_adjust=False)
        if data.empty:
            raise ValueError("No ticker tape data")

        closes = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
        if isinstance(closes, pd.Series):
            closes = closes.to_frame(name=TICKER_TAPE_LIST[0])

        results = []
        for sym in TICKER_TAPE_LIST:
            try:
                series = closes[sym].dropna()
                if len(series) < 2:
                    raise ValueError("Insufficient history")

                price = float(series.iloc[-1])
                prev = float(series.iloc[-2])
                chg = price - prev
                pct = (chg / prev) * 100 if prev else 0.0

                results.append(
                    {
                        "sym": sym,
                        "name": sym.replace(".NS", ""),
                        "price": round(price, 2),
                        "chg": round(chg, 2),
                        "pct": round(pct, 2),
                    }
                )
            except Exception:
                results.append(
                    {
                        "sym": sym,
                        "name": sym.replace(".NS", ""),
                        "price": None,
                        "chg": None,
                        "pct": None,
                    }
                )

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── AI AUDITOR (MCS) ENDPOINTS ──

@router.post("/fundamentals/mcs/seed/{ticker}")
def seed_db(ticker: str):
    """Dev endpoint to inject dummy promises. Sanitizes input to remove .NS"""
    clean_ticker = ticker.upper().replace(".NS", "")
    seed_test_data(clean_ticker)
    return {"status": "seeded", "ticker": clean_ticker}


@router.get("/fundamentals/mcs/{ticker}")
def get_management_credibility(ticker: str):
    """Fetches the MCS Score. Sanitizes input to remove .NS"""
    clean_ticker = ticker.upper().replace(".NS", "")
    
    # 1. THE FAST PATH: Check your new database first!
    cached_result = get_cached_mcs(clean_ticker)
    if cached_result:
        print(f"FAST RETRIEVAL: Loaded {clean_ticker} directly from Database!")
        return cached_result
        
    # 2. THE SLOW PATH: Not in DB. We must put the AI to work.
    print(f"NEW STOCK: Asking AI to analyze {clean_ticker}...")
    ai_result = calculate_mcs(clean_ticker)
    
    # 3. SAVE FOR LATER: Store the AI's hard work in the database
    if ai_result and ai_result.get("mcs_score") is not None:
        save_mcs_to_cache(
            ticker=clean_ticker,
            score=ai_result["mcs_score"],
            audit_data=ai_result["audits"]
        )
        print(f"SAVED: {clean_ticker} is now permanently in the Database.")
        
    return ai_result
