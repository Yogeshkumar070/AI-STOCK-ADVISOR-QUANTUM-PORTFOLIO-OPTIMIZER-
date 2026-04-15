from fastapi import APIRouter, HTTPException
from backend.ai.debate_engine import run_debate
from backend.ai.forecaster import run_forecast
from backend.ai.mcs_engine import calculate_management_score

router = APIRouter(prefix="/ai", tags=["AI Advisor"])


@router.get("/management-score/{symbol}")
def get_management_score(symbol: str):
    try:
        return calculate_management_score(symbol.upper())
    except Exception as e:
        print(f"[MCS Error] {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Management score failed: {str(e)}")


@router.get("/forecast/{symbol}")
def get_forecast(symbol: str):
    try:
        return run_forecast(symbol.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[Forecast Error] {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")


@router.get("/debate/{symbol}")
def get_debate(symbol: str):
    try:
        return run_debate(symbol.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[Debate Error] {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Debate failed: {str(e)}")
