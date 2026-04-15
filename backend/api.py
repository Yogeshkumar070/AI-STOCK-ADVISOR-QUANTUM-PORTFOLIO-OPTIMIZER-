from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import yfinance as yf
import numpy as np

from portfolio.quantum.run_quantum import run_quantum_optimization
from market.data_fetcher import fetch_stock_history
from market.indicators import compute_metrics
from portfolio.allocation.weight_engine import allocate_weights
from portfolio.backtest.backtest_engine import run_backtest
from portfolio.benchmark.nifty_compare import compare_with_nifty
from portfolio.simulation.monte_carlo import run_monte_carlo
try:
    from backend.nlp.mcs_engine import calculate_mcs, seed_test_data
except ModuleNotFoundError:
    from nlp.mcs_engine import calculate_mcs, seed_test_data

app = FastAPI(title="Quantum Portfolio API")

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ STOCK OVERVIEW ------------------
@app.get("/stock/overview/{symbol}")
def stock_overview(symbol: str):
    try:
        ticker_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        history = ticker.history(period="1y")

        if history.empty:
            raise HTTPException(status_code=400, detail="Invalid NSE symbol")

        ceo_name = "N/A"
        officers = info.get("companyOfficers", [])
        if officers and len(officers) > 0:
            ceo_name = officers[0].get("name", "N/A")

        return {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "long_business_summary": info.get("longBusinessSummary"),
            "description": info.get("longBusinessSummary"),
            "website": info.get("website"),
            "city": info.get("city"),
            "fullTimeEmployees": info.get("fullTimeEmployees"),
            "ceo": ceo_name,
            "founded_year": info.get("founded"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "revenue": info.get("totalRevenue"),
            "net_profit": info.get("netIncomeToCommon"),
            "eps": info.get("trailingEps"),
            "dividend_yield": info.get("dividendYield"),
            "price_history": [
                {
                    "Date": str(date.date()),
                    "Close": round(row["Close"], 2),
                }
                for date, row in history.iterrows()
            ],
        }

    except Exception:
        raise HTTPException(status_code=400, detail="Stock not found")

# ------------------ STOCK PRICES ------------------
@app.get("/stock/prices/{symbol}")
def stock_prices(symbol: str, period: str = "1y"):
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period=period)

        if hist.empty:
            raise HTTPException(status_code=404, detail="No price data")

        return {
            "symbol": symbol,
            "period": period,
            "prices": [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"]),
                }
                for idx, row in hist.iterrows()
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ------------------ QUANTUM OPTIMIZATION ------------------
class QuantumRequest(BaseModel):
    symbols: list[str] | None = None
    tickers: list[str] | None = None
    risk_tolerance: float = 0.5
    max_assets: int = 5


TICKER_TAPE_LIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFY.NS", "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS",
    "TITAN.NS", "BAJFINANCE.NS", "WIPRO.NS", "HCLTECH.NS", "ADANIENT.NS",
    "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "COALINDIA.NS", "BAJAJFINSV.NS",
]

INDEX_LIST = [
    {"symbols": ["^NSEI"], "label": "NIFTY 50"},
    {"symbols": ["^NSEBANK"], "label": "BANK NIFTY"},
    {"symbols": ["NIFTY_FIN_SERVICE.NS"], "label": "FIN NIFTY"},
    {"symbols": ["^BSESN"], "label": "SENSEX"},
    {"symbols": ["NIFTY_MID_SELECT.NS", "^CNXMIDCAP", "NIFTYMIDCAP150.NS"], "label": "MIDCPNIFTY"},
]


def fetch_index_snapshot(symbols: list[str]):
    last_error = None
    for candidate in symbols:
        try:
            ticker = yf.Ticker(candidate)
            hist = ticker.history(period="5d")
            if hist.empty or len(hist) < 1:
                raise ValueError("No data")

            price = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
            chg = price - prev
            pct = (chg / prev) * 100 if prev else 0

            return {
                "sym": candidate,
                "price": round(price, 2),
                "chg": round(chg, 2),
                "pct": round(pct, 2),
            }
        except Exception as exc:
            last_error = exc

    raise last_error or ValueError("No index data")


def fetch_live_returns(tickers: list[str]):
    tickers_ns = [f"{t}.NS" if not t.endswith(".NS") else t for t in tickers]
    data = yf.download(tickers_ns, period="2y", progress=False, auto_adjust=False)

    if data.empty:
        raise RuntimeError("No market data available for the selected assets.")

    prices = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers_ns[0])

    prices = prices.dropna(axis=1, how="all").dropna(how="all")
    if prices.empty:
        raise RuntimeError("Close price history could not be loaded.")

    prices.columns = [str(c).replace(".NS", "") for c in prices.columns]
    returns_df = prices.pct_change().dropna()

    if returns_df.empty:
        raise RuntimeError("Not enough price history to compute returns.")

    risk_rows = []
    for col in returns_df.columns:
        ret = returns_df[col].dropna()
        var_95 = np.percentile(ret, 5)
        tail_losses = ret[ret <= var_95]
        cvar = abs(float(tail_losses.mean())) if len(tail_losses) else 0.0
        risk_rows.append(
            {
                "symbol": col,
                "cvar_5pct": cvar,
                "amihud_illiquidity": 0.0001,
                "confidence_tier": "HIGH",
            }
        )

    return returns_df, pd.DataFrame(risk_rows)


@app.get("/stock/ticker-tape")
def ticker_tape():
    data = yf.download(TICKER_TAPE_LIST, period="5d", progress=False, auto_adjust=False)
    if data.empty:
        raise HTTPException(status_code=500, detail="Unable to load ticker tape data")

    closes = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
    if isinstance(closes, pd.Series):
        closes = closes.to_frame(name=TICKER_TAPE_LIST[0])

    results = []
    for sym in TICKER_TAPE_LIST:
        try:
            series = closes[sym].dropna()
            if len(series) < 2:
                raise ValueError("Insufficient history")

            price = float(series.iloc[-1])
            prev = float(series.iloc[-2])
            chg = price - prev
            pct = (chg / prev) * 100 if prev else 0.0

            results.append(
                {
                    "sym": sym,
                    "name": sym.replace(".NS", ""),
                    "price": round(price, 2),
                    "chg": round(chg, 2),
                    "pct": round(pct, 2),
                }
            )
        except Exception:
            results.append(
                {
                    "sym": sym,
                    "name": sym.replace(".NS", ""),
                    "price": None,
                    "chg": None,
                    "pct": None,
                }
            )

    return results


@app.get("/stock/indices")
def get_indices():
    results = []
    for idx in INDEX_LIST:
        try:
            snapshot = fetch_index_snapshot(idx["symbols"])
            results.append(
                {
                    "sym": snapshot["sym"],
                    "label": idx["label"],
                    "price": snapshot["price"],
                    "chg": snapshot["chg"],
                    "pct": snapshot["pct"],
                }
            )
        except Exception:
            results.append(
                {
                    "sym": idx["symbols"][0],
                    "label": idx["label"],
                    "price": None,
                    "chg": None,
                    "pct": None,
                }
            )

    return results


@app.post("/stock/fundamentals/mcs/seed/{ticker}")
def seed_mcs_data(ticker: str):
    seed_test_data(ticker)
    return {"status": "seeded", "ticker": ticker.upper().replace(".NS", "")}


@app.get("/stock/fundamentals/mcs/{ticker}")
def get_management_credibility(ticker: str):
    return calculate_mcs(ticker)

@app.post("/quantum/optimize")
def quantum_optimize(req: QuantumRequest):
    requested = req.tickers or req.symbols or []
    if len(requested) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 stocks for optimization")

    try:
        returns_df, risk_df = fetch_live_returns(requested)

        q_result = run_quantum_optimization(
            risk_df=risk_df,
            returns_df=returns_df,
            max_assets=req.max_assets,
            risk_factor=req.risk_tolerance,
        )

        selected_assets = q_result["selected_stocks"]
        if not selected_assets:
            raise RuntimeError("Quantum optimization returned no assets.")

        allocation = allocate_weights(
            selected_stocks=selected_assets,
            returns_df=returns_df,
            risk_aversion=req.risk_tolerance,
        )

        sel_returns = returns_df[selected_assets]
        weights_series = pd.Series(allocation["weights"])
        portfolio_returns = sel_returns.dot(weights_series)

        start_date = str(portfolio_returns.index.min().date())
        end_date = str(portfolio_returns.index.max().date())

        benchmark = compare_with_nifty(
            portfolio_returns=portfolio_returns,
            start_date=start_date,
            end_date=end_date,
        )

        backtest = run_backtest(
            weights=allocation["weights"],
            returns_df=returns_df,
        )

        monte_carlo = run_monte_carlo(portfolio_returns=portfolio_returns)

        return {
            "status": "Optimal",
            "input_assets": requested,
            "tickers": selected_assets,
            "selected_stocks": selected_assets,
            "num_selected": len(selected_assets),
            "weights": allocation["weights"],
            "metrics": {
                "expected_return": allocation["expected_return"],
                "portfolio_volatility": allocation["volatility"],
                "sharpe_ratio": allocation["sharpe_ratio"],
            },
            "quantum_details": q_result.get("quantum_metadata", {}),
            "correlation_matrix": q_result.get("correlation_matrix"),
            "benchmark_comparison": benchmark,
            "backtest": backtest,
            "monte_carlo": monte_carlo,
            "risk_contribution": allocation.get("risk_contribution", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
