
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
import yfinance as yf

# ---- ENGINE IMPORTS ----
# Ensure these files exist in your project.
from backend.portfolio.quantum.run_quantum import run_quantum_optimization
from backend.portfolio.allocation.weight_engine import allocate_weights
from backend.portfolio.backtest.backtest_engine import run_backtest
from backend.portfolio.benchmark.nifty_compare import compare_with_nifty
from backend.portfolio.simulation.monte_carlo import run_monte_carlo

router = APIRouter(prefix="/quantum", tags=["Quantum Portfolio"])

# -------------------------
# Request Model
# -------------------------
class QuantumRequest(BaseModel):
    tickers: List[str]
    risk_tolerance: float = 0.5
    max_assets: int = 5

# -------------------------
# Helper: Fetch Live Data
# -------------------------
def fetch_live_data(tickers: list[str]):
    """
    Downloads live data from Yahoo Finance and calculates ACTUAL Returns + Risk Metrics.
    """
    tickers_ns = [f"{t}.NS" if not t.endswith(".NS") else t for t in tickers]
    print(f"📥 Downloading live data for: {tickers_ns}")
    
    try:
        # Download Data
        data = yf.download(tickers_ns, period="2y", progress=False)
        
        if isinstance(data.columns, pd.MultiIndex):
            prices = data["Close"]
        else:
            prices = data["Close"] if "Close" in data else data
            
        prices.columns = [c.replace(".NS", "") for c in prices.columns]
        
        # Calculate Returns
        returns_df = prices.pct_change().dropna()
        
        if returns_df.empty:
            raise ValueError("No price data found from Yahoo Finance")

        # 🟢 CALCULATE REAL RISK METRICS
        risk_metrics = []
        for col in returns_df.columns:
            ret = returns_df[col]
            vol = ret.std()
            
            # 1. Real CVaR (95% Confidence)
            # Find the 5th percentile worst return, then average the returns that are worse than that
            var_95 = np.percentile(ret, 5)
            tail_losses = ret[ret <= var_95]
            cvar = abs(tail_losses.mean()) if len(tail_losses) > 0 else 0.0
            
            # 2. Basic Illiquidity Metric (Using proxy zero for large cap Nifty50, or calculate if volume data exists)
            illiq = 0.0001 
            
            risk_metrics.append({
                "symbol": col,
                "cvar_5pct": cvar,
                "amihud_illiquidity": illiq,
                "confidence_tier": "HIGH"
            })
            
        risk_df = pd.DataFrame(risk_metrics)
        return returns_df, risk_df

    except Exception as e:
        print(f"Data Download Error: {e}")
        raise RuntimeError(f"Failed to download market data: {str(e)}")
    

# -------------------------
# Quantum Optimize Endpoint
# -------------------------
@router.post("/optimize")
def optimize_quantum_portfolio(req: QuantumRequest):

    if len(req.tickers) < 2:
        raise HTTPException(
            status_code=400, 
            detail="Select at least 2 stocks for optimization"
        )

    try:
        # 1️⃣ FETCH LIVE DATA (Replaces CSV loading)
        returns_df, risk_df = fetch_live_data(req.tickers)

        # 2️⃣ QUANTUM ASSET SELECTION
        q_result = run_quantum_optimization(
            risk_df=risk_df,
            returns_df=returns_df,
            max_assets=req.max_assets,
            risk_factor=req.risk_tolerance,
        )

        selected_assets = q_result["selected_stocks"]

        if not selected_assets:
            raise RuntimeError("Quantum optimization returned no assets.")

        # 3️⃣ CLASSICAL WEIGHT ALLOCATION
        allocation = allocate_weights(
            selected_stocks=selected_assets,
            returns_df=returns_df,
            risk_aversion=req.risk_tolerance
        )

        # 4️⃣ CALCULATE PORTFOLIO RETURNS
        sel_returns = returns_df[selected_assets]
        weights_series = pd.Series(allocation["weights"])
        portfolio_returns = sel_returns.dot(weights_series)

        # 5️⃣ BENCHMARK COMPARISON
        start_date = str(portfolio_returns.index.min().date())
        end_date = str(portfolio_returns.index.max().date())
        
        benchmark = compare_with_nifty(
            portfolio_returns=portfolio_returns,
            start_date=start_date,
            end_date=end_date
        )

        # 6️⃣ BACKTEST
        backtest = run_backtest(
            weights=allocation["weights"],
            returns_df=returns_df
        )

        # 7️⃣ MONTE CARLO
        monte_carlo = run_monte_carlo(
            portfolio_returns=portfolio_returns
        )

        # 8️⃣ FINAL RESPONSE
        return {
            "status": "Optimal",
            "tickers": selected_assets,
            "weights": allocation["weights"],
            "metrics": {
                "expected_return": allocation["expected_return"],
                "portfolio_volatility": allocation["volatility"],
                "sharpe_ratio": allocation["sharpe_ratio"],
            },
            "quantum_details": q_result["quantum_metadata"],
            "correlation_matrix": q_result.get("correlation_matrix"),
            "benchmark_comparison": benchmark,
            "backtest": backtest,
            "monte_carlo": monte_carlo,
            "risk_contribution": allocation.get("risk_contribution", {})
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        # Return the actual error message to the frontend for easier debugging
        raise HTTPException(status_code=500, detail=str(e))