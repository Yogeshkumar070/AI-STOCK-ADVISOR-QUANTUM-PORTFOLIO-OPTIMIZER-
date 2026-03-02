import numpy as np
import pandas as pd
from backend.portfolio.allocation.weight_engine import allocate_weights


def generate_efficient_frontier(selected_stocks, returns_df):
    """
    Generates efficient frontier points by varying risk_aversion.
    """

    frontier_points = []

    risk_levels = np.linspace(0.1, 0.9, 15)

    for r in risk_levels:
        allocation = allocate_weights(
            selected_stocks=selected_stocks,
            returns_df=returns_df,
            risk_aversion=r
        )

        frontier_points.append({
            "risk_aversion": round(float(r), 2),
            "volatility": allocation["volatility"],
            "return": allocation["expected_return"],
            "sharpe": allocation["sharpe_ratio"]
        })

    return frontier_points