import numpy as np
import pandas as pd

def run_monte_carlo(portfolio_returns: pd.Series, num_simulations=10000, time_horizon=252, initial_investment=100):
    """
    Runs a Geometric Brownian Motion (GBM) Monte Carlo simulation.
    Returns realistic expected values and tail-risk probabilities.
    """
    if portfolio_returns.empty:
        return {"expected_value": 0, "best_case": 0, "worst_case": 0, "probability_of_loss": 0}

    # Calculate daily drift (mean) and volatility (standard deviation)
    mu = portfolio_returns.mean()
    vol = portfolio_returns.std()

    # GBM Formula components
    drift = (mu - 0.5 * vol**2) * time_horizon
    diffusion = vol * np.sqrt(time_horizon)
    
    # Generate 10,000 random standard normal variables
    Z = np.random.normal(0, 1, num_simulations)
    
    # Calculate the terminal value for all 10,000 simulations simultaneously
    simulated_end_values = initial_investment * np.exp(drift + diffusion * Z)

    # Extract Metrics for the Frontend
    expected_value = np.mean(simulated_end_values)
    best_case = np.percentile(simulated_end_values, 95)  # Top 5% outcome
    worst_case = np.percentile(simulated_end_values, 5)   # Bottom 5% outcome
    
    # Calculate exact probability of losing money
    loss_events = np.sum(simulated_end_values < initial_investment)
    prob_loss = (loss_events / num_simulations) * 100

    return {
        "expected_value": round(expected_value, 2),
        "best_case": round(best_case, 2),
        "worst_case": round(worst_case, 2),
        "probability_of_loss": round(prob_loss, 2)
    }