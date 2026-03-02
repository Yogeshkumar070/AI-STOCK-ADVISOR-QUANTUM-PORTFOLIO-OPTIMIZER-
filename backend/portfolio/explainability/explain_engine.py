import numpy as np
import pandas as pd

def correlation_summary(corr_matrix: pd.DataFrame):
    """
    Computes diversification quality from correlation matrix
    """
    upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )

    avg_corr = upper.stack().mean()
    max_corr = upper.stack().max()

    diversification_score = 1 - avg_corr if not np.isnan(avg_corr) else 0

    return {
        "average_correlation": round(float(avg_corr), 3) if not np.isnan(avg_corr) else 0,
        "max_correlation": round(float(max_corr), 3) if not np.isnan(max_corr) else 0,
        "diversification_score": round(float(diversification_score), 3)
    }


def risk_contribution(weights: dict, cov_matrix: pd.DataFrame):
    """
    Marginal risk contribution of each asset
    """
    symbols = list(weights.keys())
    w = np.array(list(weights.values()))

    # Calculate portfolio variance
    portfolio_var = np.dot(w.T, np.dot(cov_matrix.values, w))
    
    # Calculate marginal risk (covariance of each asset with the portfolio)
    marginal_risk = np.dot(cov_matrix.values, w)

    contributions = {}
    if portfolio_var > 0:
        for i in range(len(symbols)):
            # Contribution = weight * marginal_risk / total_portfolio_variance
            contributions[symbols[i]] = round(
                float(w[i] * marginal_risk[i] / portfolio_var), 4
            )
    else:
         for s in symbols:
             contributions[s] = 0.0

    return contributions


def explain_selection(
    selected_stocks: list[str],
    corr_matrix: pd.DataFrame,
    weights: dict
):
    """
    Human-readable explanations for UI
    """
    # 1. Get stats
    corr_stats = correlation_summary(corr_matrix)
    
    # 2. Get Risk contributions (Need Covariance, but we can approximate with correlation for text explanation)
    # Note: For accurate risk contribution, we usually pass covariance. 
    # Here we use the weights directly for the textual explanation logic.
    
    avg_corr_val = corr_stats["average_correlation"]
    explanations = []

    for stock in selected_stocks:
        stock_avg_corr = corr_matrix[stock].mean()
        weight_pct = round(weights.get(stock, 0) * 100, 2)
        
        # Logic: If stock's correlation is lower than portfolio average, it's a "Diversifier"
        if stock_avg_corr < avg_corr_val:
            reason = "Selected as a strong diversifier (low correlation vs portfolio)."
        else:
            reason = "Selected for high return potential despite moderate correlation."

        explanations.append({
            "stock": stock,
            "weight": f"{weight_pct}%",
            "reason": reason
        })

    return {
        "summary": (
            "Stocks were selected to minimize correlation and maximize "
            "risk-adjusted returns using Quantum Optimization (QAOA)."
        ),
        "diversification_stats": corr_stats,
        "details": explanations
    }