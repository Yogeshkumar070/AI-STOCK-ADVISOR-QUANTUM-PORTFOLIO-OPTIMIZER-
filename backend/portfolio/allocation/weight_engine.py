import numpy as np
import pandas as pd
from scipy.optimize import minimize


# -------------------------------
# CVaR Calculation (Fast Numpy)
# -------------------------------
def portfolio_cvar(weights, returns_array, alpha=0.95):
    portfolio_returns = np.dot(returns_array, weights)
    var_level = np.percentile(portfolio_returns, (1 - alpha) * 100)
    tail_losses = portfolio_returns[portfolio_returns <= var_level]

    if len(tail_losses) == 0:
        return 0.0

    return abs(tail_losses.mean())


# -------------------------------
# Max Drawdown (Fast Numpy)
# -------------------------------
def portfolio_max_drawdown(weights, returns_array):
    portfolio_returns = np.dot(returns_array, weights)

    log_returns = np.log1p(portfolio_returns)
    equity = np.exp(np.cumsum(log_returns))

    rolling_max = np.maximum.accumulate(equity)
    drawdown = (equity / rolling_max) - 1

    return abs(drawdown.min())


# -------------------------------
# Multi-Factor Institutional Objective
# -------------------------------
def portfolio_objective(
    weights,
    mean_returns,
    cov_matrix,
    returns_array,
    risk_aversion
):
    portfolio_return = np.dot(weights, mean_returns)
    portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
    portfolio_cvar_value = portfolio_cvar(weights, returns_array)
    portfolio_dd = portfolio_max_drawdown(weights, returns_array)

    # Institutional coefficients
    lambda_var = risk_aversion
    lambda_cvar = 0.5
    lambda_dd = 0.6
    lambda_ret = (1 - risk_aversion)

    return (
        lambda_var * portfolio_variance
        + lambda_cvar * portfolio_cvar_value
        + lambda_dd * portfolio_dd
        - lambda_ret * portfolio_return
    )


# -------------------------------
# Risk Contribution
# -------------------------------
def calculate_risk_contribution(weights: dict, returns_df: pd.DataFrame):
    if not weights:
        return {}

    assets = list(weights.keys())
    w = np.array(list(weights.values()))
    cov = returns_df[assets].cov().values * 252

    portfolio_var = np.dot(w.T, np.dot(cov, w))

    if portfolio_var <= 0:
        return {k: 0.0 for k in assets}

    mrc = np.dot(cov, w)
    trc = (w * mrc) / portfolio_var

    return {
        k: round(float(trc[i]), 4)
        for i, k in enumerate(assets)
    }


# -------------------------------
# Allocation Engine (Final Version)
# -------------------------------
def allocate_weights(
    selected_stocks: list[str],
    returns_df: pd.DataFrame,
    risk_aversion: float = 0.6
):

    if len(selected_stocks) < 2:
        return {
            "weights": {selected_stocks[0]: 1.0},
            "expected_return": 0,
            "volatility": 0,
            "sharpe_ratio": 0,
            "risk_contribution": {selected_stocks[0]: 1.0},
            "allocation_method": "Single Asset",
            "risk_profile": "N/A"
        }

    returns = returns_df[selected_stocks].dropna()

    mean_returns = returns.mean().values * 252
    cov_matrix = returns.cov().values * 252
    returns_array = returns.values

    num_assets = len(selected_stocks)

    init_weights = np.ones(num_assets) / num_assets

    # Diversification Constraints
    min_weight = 0.05
    max_weight = 0.50
    bounds = tuple((min_weight, max_weight) for _ in range(num_assets))

    constraints = ({
        'type': 'eq',
        'fun': lambda w: np.sum(w) - 1
    })

    try:
        result = minimize(
            portfolio_objective,
            init_weights,
            args=(mean_returns, cov_matrix, returns_array, risk_aversion),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 200}
        )

        weights_array = result.x if result.success else init_weights

    except Exception as e:
        print(f"Optimization Error: {e}")
        weights_array = init_weights

    # Normalize safety
    weights_array = weights_array / np.sum(weights_array)

    portfolio_return = float(np.dot(weights_array, mean_returns))
    portfolio_volatility = float(
        np.sqrt(np.dot(weights_array.T, np.dot(cov_matrix, weights_array)))
    )

    sharpe_ratio = (
        portfolio_return / portfolio_volatility
        if portfolio_volatility > 0 else 0
    )

    weights_dict = {
        selected_stocks[i]: round(float(weights_array[i]), 4)
        for i in range(num_assets)
    }

    return {
        "weights": weights_dict,
        "expected_return": round(portfolio_return * 100, 2),
        "volatility": round(portfolio_volatility * 100, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "risk_contribution": calculate_risk_contribution(weights_dict, returns_df),
        "allocation_method": "Institutional Multi-Factor (Var + CVaR + Drawdown)",
        "risk_profile": (
            "Conservative" if risk_aversion > 0.7
            else "Balanced" if risk_aversion > 0.4
            else "Aggressive"
        )
    }