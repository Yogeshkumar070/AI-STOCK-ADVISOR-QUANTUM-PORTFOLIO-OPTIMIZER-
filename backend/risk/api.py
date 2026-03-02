# backend/risk/api.py

from fastapi import APIRouter, HTTPException
import pandas as pd
import yfinance as yf

from backend.risk.cvar import compute_cvar
from backend.risk.drawdown import compute_max_drawdown
from backend.risk.liquidity import compute_amihud_illiquidity

router = APIRouter(prefix="/risk", tags=["Risk"])

@router.get("/{symbol}")
def get_risk_metrics(symbol: str):
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="2y")

        if hist.empty:
            raise Exception("No price data")

        returns = hist["Close"].pct_change().dropna()

        return {
            "symbol": symbol,
            "cvar_95": round(compute_cvar(returns, alpha=0.05) * 100, 2),
            "max_drawdown": round(compute_max_drawdown(hist["Close"]) * 100, 2),
            "amihud_illiquidity": round(compute_amihud_illiquidity(hist), 6),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
