from fastapi import APIRouter, HTTPException
import yfinance as yf
import pandas as pd

router = APIRouter()

# ------------------ STOCK OVERVIEW ------------------
@router.get("/overview/{symbol}")
def stock_overview(symbol: str):
    try:
        # 1. Handle Symbol Format
        ticker_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
        ticker = yf.Ticker(ticker_symbol)

        # 2. Fetch History (1 Year)
        history = ticker.history(period="1y")

        if history.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"Stock {symbol} not found or delisted."
            )

        # 3. Fetch Fundamentals
        info = ticker.info

        # 4. Try to extract CEO (YFinance stores this in a list of officers)
        ceo_name = "N/A"
        officers = info.get("companyOfficers", [])
        if officers and len(officers) > 0:
            ceo_name = officers[0].get("name", "N/A")

        # 5. Return Data (NOW INCLUDING TEXT/PROFILE DATA)
        return {
            "symbol": symbol,
            
            # --- NEW: Company Profile Data ---
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "long_business_summary": info.get("longBusinessSummary"),
            "website": info.get("website"),
            "city": info.get("city"),
            "fullTimeEmployees": info.get("fullTimeEmployees"),
            "ceo": ceo_name,
            
            # --- Financials ---
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "revenue": info.get("totalRevenue"),
            "eps": info.get("trailingEps"),
            "dividend_yield": info.get("dividendYield"),
            
            # --- Price History ---
            "price_history": [
                {
                    "Date": str(date.date()),
                    "Close": round(row["Close"], 2)
                }
                for date, row in history.iterrows()
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching stock data")

# ------------------ STOCK PRICES (FOR CANDLESTICK/CHARTS) ------------------
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