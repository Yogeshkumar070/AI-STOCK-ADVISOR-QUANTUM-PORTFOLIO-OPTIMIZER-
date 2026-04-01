from fastapi import APIRouter, HTTPException
from backend.ai.management_score import calculate_management_score
from backend.ai.debate_engine import run_bull_bear_debate

router = APIRouter(prefix="/ai", tags=["AI Advisor"])


@router.get("/management-score/{symbol}")
def get_management_score(symbol: str):
    try:
        return calculate_management_score(symbol.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[MCS Error] {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Management score analysis failed: {str(e)}")


@router.get("/debate/{symbol}")
def get_debate(symbol: str):
    try:
        return run_bull_bear_debate(symbol.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[Debate Error] {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Debate engine failed: {str(e)}")
