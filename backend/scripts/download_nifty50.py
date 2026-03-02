import yfinance as yf
import os

NIFTY_50 = "TMPV"

os.makedirs("data/raw/prices", exist_ok=True)

for stock in NIFTY_50:
    print(f"Downloading {stock}")
    df = yf.download(f"{stock}.NS", period="5y")
    if not df.empty:
        df.to_csv(f"data/raw/prices/{stock}_NS.csv")
