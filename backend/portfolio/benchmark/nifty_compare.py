import yfinance as yf
import pandas as pd
import numpy as np

def normalize_series(returns: pd.Series, base: float = 100):
    return base * (1 + returns).cumprod()

def calculate_beta(portfolio_returns, benchmark_returns):
    covariance = np.cov(portfolio_returns, benchmark_returns)[0][1]
    benchmark_variance = np.var(benchmark_returns)
    return covariance / benchmark_variance if benchmark_variance > 0 else 0

def compare_with_nifty(
    portfolio_returns: pd.Series,
    start_date: str,
    end_date: str
):
    try:
        nifty_df = yf.download("^NSEI", start=start_date, end=end_date, progress=False)

        if isinstance(nifty_df.columns, pd.MultiIndex):
            nifty_close = nifty_df["Close"]["^NSEI"]
        else:
            nifty_close = nifty_df["Close"]

        nifty_returns = nifty_close.pct_change().dropna()

        aligned = pd.concat([portfolio_returns, nifty_returns], axis=1, join="inner")
        aligned.columns = ["portfolio", "nifty"]

        if aligned.empty:
            return None

        port_equity = normalize_series(aligned["portfolio"])
        nifty_equity = normalize_series(aligned["nifty"])

        # ===== NEW: BETA CALCULATION =====
        beta = calculate_beta(aligned["portfolio"], aligned["nifty"])

        return {
            "equity_curve": {
                "dates": port_equity.index.strftime("%Y-%m-%d").tolist(),
                "portfolio": port_equity.round(2).tolist(),
                "nifty": nifty_equity.round(2).tolist(),
            },
            "portfolio_metrics": {
                "annual_return": round(aligned["portfolio"].mean() * 252 * 100, 2),
                "volatility": round(aligned["portfolio"].std() * np.sqrt(252) * 100, 2),
            },
            "nifty_metrics": {
                "annual_return": round(aligned["nifty"].mean() * 252 * 100, 2),
                "volatility": round(aligned["nifty"].std() * np.sqrt(252) * 100, 2),
            },
            "beta_vs_nifty": round(float(beta), 3)
        }

    except Exception as e:
        print(f"Benchmark Error: {e}")
        return None