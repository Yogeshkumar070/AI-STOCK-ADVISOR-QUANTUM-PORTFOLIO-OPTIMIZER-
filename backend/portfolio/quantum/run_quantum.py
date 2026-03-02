import numpy as np
import pandas as pd

from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms.minimum_eigensolvers import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler


def run_quantum_optimization(
    risk_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    max_assets: int = 5,
    risk_factor: float = 0.6,
    return_factor: float = 0.4
):
    """
    =================================
    QUANTUM STOCK SELECTION ENGINE
    =================================

    ✔ Selects optimal subset of stocks
    ✔ Penalizes correlation (diversification)
    ✔ Balances risk vs return
    ❌ NO weight allocation (done classically)
    """

    # ----------------------------
    # 1️⃣ Validation
    # ----------------------------
    symbols = risk_df["symbol"].tolist()
    n = len(symbols)

    if n < 2:
        raise ValueError("Quantum optimization requires at least 2 assets")

    max_assets = min(max_assets, n)

    # ----------------------------
    # 2️⃣ Statistics
    # ----------------------------
    mean_returns = returns_df.mean() * 252
    corr_matrix = returns_df.corr().fillna(0.0)

    # ----------------------------
    # 3️⃣ QUBO Formulation
    # ----------------------------
    qp = QuadraticProgram()

    for i in range(n):
        qp.binary_var(name=f"x{i}")

    confidence_penalty = {
        "HIGH": 0.0,
        "MEDIUM": 0.15,
        "LOW": 0.35
    }

    linear = {}
    quadratic = {}

    # Risk − Return
    for i in range(n):
        cvar = abs(risk_df.loc[i, "cvar_5pct"])
        illiq = risk_df.loc[i, "amihud_illiquidity"]
        conf = confidence_penalty.get(
            risk_df.loc[i, "confidence_tier"], 0.5
        )

        linear[f"x{i}"] = (
            risk_factor * (cvar + illiq + conf)
            - return_factor * mean_returns.iloc[i]
        )

    # Diversification penalty
    for i in range(n):
        for j in range(i + 1, n):
            corr = abs(corr_matrix.iloc[i, j])
            quadratic[(f"x{i}", f"x{j}")] = risk_factor * corr

    qp.minimize(linear=linear, quadratic=quadratic)

    # ----------------------------
    # 4️⃣ Asset Budget Constraint
    # ----------------------------
    qp.linear_constraint(
        linear={f"x{i}": 1 for i in range(n)},
        sense="==",
        rhs=max_assets,
        name="asset_budget"
    )

    # ----------------------------
    # 5️⃣ QAOA Solve
    # ----------------------------
    sampler = StatevectorSampler()

    qaoa = QAOA(
        sampler=sampler,
        optimizer=COBYLA(maxiter=50),
        reps=1
    )

    optimizer = MinimumEigenOptimizer(qaoa)
    result = optimizer.solve(qp)

    solution = np.array(result.x, dtype=int)

    selected_indices = np.where(solution == 1)[0].tolist()
    selected_assets = [symbols[i] for i in selected_indices]

    # ----------------------------
    # 6️⃣ Explainability Metadata
    # ----------------------------
    avg_corr = (
        corr_matrix.iloc[selected_indices, selected_indices].values.mean()
        if len(selected_indices) > 1 else 0.0
    )

    # ----------------------------
    # 7️⃣ Return (API-safe)
    # ----------------------------
    return {
        "selected_stocks": selected_assets,
        "num_selected": int(solution.sum()),
        "correlation_matrix": corr_matrix
            .iloc[selected_indices, selected_indices]
            .round(3)
            .to_dict(),
        "quantum_metadata": {
            "algorithm": "QAOA",
            "backend": "StatevectorSimulator",
            "objective": "Risk + Return + Diversification (QUBO)",
            "risk_factor": risk_factor,
            "return_factor": return_factor,
            "diversification_score": round(1 - avg_corr, 3)
        }
    }
