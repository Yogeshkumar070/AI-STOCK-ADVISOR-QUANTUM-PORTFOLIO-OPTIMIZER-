from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()  # loads ANTHROPIC_API_KEY from .env at project root

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

# Quantum Router already has prefix="/quantum" inside quantum.py, so we don't add it here
app.include_router(quantum_router)

# Risk Router has prefix="/risk" inside api.py, so we don't add it here
app.include_router(risk_router)

# Stocks Router DOES NOT have a prefix in stocks.py, so we MUST ADD IT HERE
app.include_router(stocks_router, prefix="/stock", tags=["Stocks"])

# AI Advisor Router has prefix="/ai" inside ai_advisor.py
app.include_router(ai_router)

@app.get("/")
def health_check():
    return {"status": "FinNet Backend Running"}


    