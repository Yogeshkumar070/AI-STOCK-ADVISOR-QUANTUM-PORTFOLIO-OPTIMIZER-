import yfinance as yf
import pandas as pd

def get_stock_overview(symbol: str):
    ticker = yf.Ticker(symbol + ".NS")

    info = ticker.info
    hist = ticker.history(period="1y")

    if hist.empty:
        raise ValueError("Invalid stock symbol")

    price_data = [
        {
            "date": str(idx.date()),
            "close": round(row["Close"], 2)
        }
        for idx, row in hist.iterrows()
    ]

    return {
        "symbol": symbol,
        "company_name": info.get("longName"),
        "current_price": info.get("currentPrice"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        
        "price_history": [
  { "Date": "...", "Close": 2456.3 },
  { "Date": "...", "Close": 2471.9 }
]

    }
