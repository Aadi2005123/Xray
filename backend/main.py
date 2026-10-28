"""
Main FastAPI application entry point.
Configures CORS, lifespan events (model pre-warming), and route mounting.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path regardless of execution CWD
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import logging
from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config.settings import CORS_ORIGINS, MEDICAL_DISCLAIMER
from backend.api.routes import router
from backend.ml.factory import get_model
from backend.services.analysis_service import AnalysisService

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup & shutdown lifecycle management.
    Pre-warms and caches the CXR model once at startup to avoid per-request latency.
    """
    logger.info("Initializing Chest X-Ray AI Application...")
    model = get_model()
    app.state.model = model
    app.state.analysis_service = AnalysisService(model)
    logger.info("Model loaded successfully into app.state.")
    logger.info("Configured CORS allowed origins: %s", CORS_ORIGINS)
    yield
    logger.info("Shutting down Chest X-Ray AI backend...")


app = FastAPI(
    title="Chest X-Ray Disease Detection API",
    description="Explainable Real-Time Chest Radiograph Analysis using Deep Learning.",
    version="1.0.0",
    lifespan=lifespan,
)

# Secure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Custom global exception handler: never leak stack traces to clients
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception processing %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )

# Include API endpoints
app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "Chest X-Ray Disease Detection API",
        "version": "1.0.0",
        "documentation": "/docs",
        "disclaimer": MEDICAL_DISCLAIMER,
    }


if __name__ == "__main__":
    import sys
    import uvicorn
    from backend.config.settings import HOST, PORT

    logger.info("Starting CXR server on %s:%s...", HOST, PORT)
    try:
        uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)
    except OSError as e:
        logger.error(
            "Port binding failure for %s:%s: %s. "
            "Please ensure port %s is not already occupied by another service.",
            HOST, PORT, e, PORT,
        )
        sys.exit(1)

