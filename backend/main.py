from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Routers
from backend.routers.quantum import router as quantum_router
from backend.risk.api import router as risk_router
from backend.routers.stocks import router as stocks_router
from backend.routers.ai_advisor import router as ai_router

app = FastAPI(title="FinNet Backend")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTER ROUTERS ---
app.include_router(quantum_router)
app.include_router(risk_router)
app.include_router(stocks_router, prefix="/stock", tags=["Stocks"])
app.include_router(ai_router)

@app.get("/")
def health_check():
    return {"status": "FinNet Backend Running"}
