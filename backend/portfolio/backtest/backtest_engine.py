import numpy as np
import pandas as pd


# ----------------------------------
# Institutional-Grade Backtest Engine
# ----------------------------------
def run_backtest(
    weights: dict,
    returns_df: pd.DataFrame,
):
    """
    PROFESSIONAL PORTFOLIO BACKTEST ENGINE

    - Uses log returns for stability
    - Generates normalized equity curve (start at 100)
    - Computes CAGR, Volatility, Sharpe, Max Drawdown
    """

    # -------------------------------
    # 1️⃣ Data Alignment
    # -------------------------------
    assets = list(weights.keys())
    valid_assets = [a for a in assets if a in returns_df.columns]

    if not valid_assets:
        return {}

    returns = returns_df[valid_assets].dropna()
    w = np.array([weights[a] for a in valid_assets])

    # Normalize weights if needed
    if w.sum() > 0:
        w = w / w.sum()

    # -------------------------------
    # 2️⃣ Portfolio Log Returns
    # -------------------------------
    portfolio_returns = returns.dot(w)

    # Convert to log returns for compounding stability
    log_returns = np.log1p(portfolio_returns)

    # -------------------------------
    # 3️⃣ Equity Curve (Normalized to 100)
    # -------------------------------
    equity_curve = np.exp(log_returns.cumsum()) * 100

    # -------------------------------
    # 4️⃣ Drawdown Calculation
    # -------------------------------
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve / rolling_max) - 1
    max_drawdown = float(drawdown.min())

    # -------------------------------
    # 5️⃣ Performance Metrics
    # -------------------------------
    trading_days = 252
    total_days = len(portfolio_returns)

    total_return = (equity_curve.iloc[-1] / 100) - 1

    years = total_days / trading_days

    if years > 0:
        cagr = (equity_curve.iloc[-1] / 100) ** (1 / years) - 1
    else:
        cagr = 0

    annual_volatility = float(portfolio_returns.std() * np.sqrt(trading_days))

    sharpe_ratio = (
        (cagr / annual_volatility)
        if annual_volatility > 0
        else 0
    )

    # -------------------------------
    # 6️⃣ Output Structure
    # -------------------------------
    return {
        "equity_curve": {
            "dates": equity_curve.index.astype(str).tolist(),
            "portfolio": equity_curve.round(2).tolist(),
            "drawdown": drawdown.round(4).tolist()
        },
        "metrics": {
            "cumulative_return_pct": round(total_return * 100, 2),
            "cagr_pct": round(cagr * 100, 2),
            "volatility_pct": round(annual_volatility * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
        },
        # Flat values for simpler access
        "cagr": round(cagr * 100, 2),
        "max_drawdown": round(max_drawdown * 100, 2),
        "sharpe_ratio": round(sharpe_ratio, 2)
    }