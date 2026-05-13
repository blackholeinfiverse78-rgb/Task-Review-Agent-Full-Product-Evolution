"""
Task Review AI - Production
Version: 1.1.1
"""
import sys
import os

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api import lifecycle, tts, production, review_routes
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("task_review_system")

app = FastAPI(
    title="Task Review AI - Production v1.0",
    description="Deterministic Engineering Task Analysis System — [DFA VERIFIED | CORE LOCKED]",
    version="1.0.0"
)

# Security: CORS Middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", '["*"]')
try:
    origins = json.loads(allowed_origins)
except (json.JSONDecodeError, ValueError):
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Standardized failure contract as requested by the user
    errors = [f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "score": 0,
            "readiness_percent": 0,
            "status": "fail",
            "failure_reasons": ["Validation Failure"] + errors,
            "improvement_hints": ["Ensure all fields meet length requirements (Title: 5-100, Desc: 10-2000, Name: 2-50)."],
            "analysis": {
                "technical_quality": 0,
                "clarity": 0,
                "discipline_signals": 0
            },
            "meta": {
                "evaluation_time_ms": 0,
                "mode": "rule"
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.critical(f"FATAL: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "System encountered an error. Please contact the demo team."}
    )

app.include_router(lifecycle.router, prefix="/api/v1", tags=["Lifecycle"])
app.include_router(tts.router, prefix="/api/v1", tags=["TTS"])
app.include_router(production.router, prefix="/api/v1", tags=["Production"])
app.include_router(review_routes.router)


@app.get("/")
async def root():
    return {
        "message": "Parikshak Production System Online",
        "documentation": "/docs",
        "health": "/health",
        "production_status": "/api/v1/production/system/production-status",
        "niyantran_endpoint": "/api/v1/production/niyantran/submit",
        "version": "1.1.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.1.0"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
