from pathlib import Path
from datetime import datetime
import pandas as pd

from backend.utils.path_config import PRICE_DATA_DIR
from backend.risk.cvar import compute_cvar
from backend.risk.liquidity import compute_amihud_illiquidity
from backend.risk.drawdown import compute_max_drawdown


def compute_daily_returns(df: pd.DataFrame) -> pd.Series:
    return df["Close"].pct_change()


# ================= PORTFOLIO RISK (USED BY QUANTUM) =================

def calculate_portfolio_risk(
    tickers: list[str],
    weights: dict[str, float]
) -> dict:

    risk_path = (
        Path(__file__).resolve().parents[2]
        / "data" / "processed" / "risk_metrics.csv"
    )

    risk_df = pd.read_csv(risk_path)
    risk_df = risk_df[risk_df["symbol"].isin(tickers)]

    if risk_df.empty:
        raise RuntimeError("Risk metrics not found for selected tickers")

    risk_df["weight"] = risk_df["symbol"].map(weights)

    return {
        "cvar_5pct": float((risk_df["cvar_5pct"] * risk_df["weight"]).sum()),
        "illiquidity": float((risk_df["amihud_illiquidity"] * risk_df["weight"]).sum()),
        "max_drawdown": float((risk_df["max_drawdown"] * risk_df["weight"]).sum()),
    }


# ================= OFFLINE RISK ENGINE =================

def run_risk_engine():
    records = []

    price_files = list(PRICE_DATA_DIR.glob("*.csv"))
    if not price_files:
        raise RuntimeError("No price files found")

    for file_path in price_files:
        symbol = file_path.stem

        try:
            df = pd.read_csv(file_path)

            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.sort_values("Date")

            returns = compute_daily_returns(df)

            records.append({
                "symbol": symbol,
                "cvar_5pct": compute_cvar(returns, alpha=0.05),
                "amihud_illiquidity": compute_amihud_illiquidity(df),
                "max_drawdown": compute_max_drawdown(df["Close"]),
                "last_updated": datetime.today().strftime("%Y-%m-%d"),
            })

        except Exception as e:
            print(f"Risk calc failed for {symbol}: {e}")

    output_path = (
        Path(__file__).resolve().parents[2]
        / "data" / "processed" / "risk_metrics.csv"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(output_path, index=False)

    print(f"✅ Risk metrics saved → {output_path}")
