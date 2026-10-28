"""
Backend configuration loaded from environment variables.
No secrets in source code.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend/.env is loaded regardless of current working directory
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = _BACKEND_DIR / ".env"
if _ENV_PATH.exists():
    load_dotenv(dotenv_path=_ENV_PATH)
else:
    load_dotenv()

# --- Server ---
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))

# --- CORS ---
DEFAULT_CORS_ORIGINS: list[str] = [
    "https://xray-frontend-ih1b.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

_raw_cors = os.getenv("CORS_ORIGINS", "").strip()
if _raw_cors:
    _env_origins = [
        origin.strip().rstrip("/")
        for origin in _raw_cors.split(",")
        if origin.strip()
    ]
    CORS_ORIGINS: list[str] = list(dict.fromkeys(DEFAULT_CORS_ORIGINS + _env_origins))
else:
    CORS_ORIGINS = DEFAULT_CORS_ORIGINS

# --- Upload limits ---
MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))  # 10 MB

ALLOWED_MIME_TYPES: set[str] = {"image/png", "image/jpeg", "image/webp"}
ALLOWED_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".webp"}

# --- ML ---
MODEL_MODE: str = os.getenv("MODEL_MODE", "demo").strip().lower()  # "real" | "demo"
MODEL_INPUT_SIZE: int = int(os.getenv("MODEL_INPUT_SIZE", "224"))

_raw_model_path = os.getenv("MODEL_PATH", "").strip()
if _raw_model_path:
    # Resolve relative to backend directory or repo root if needed
    _candidate = Path(_raw_model_path)
    if not _candidate.is_absolute():
        if (_BACKEND_DIR / _candidate).exists():
            MODEL_PATH: str = str((_BACKEND_DIR / _candidate).resolve())
        elif (_BACKEND_DIR.parent / _candidate).exists():
            MODEL_PATH = str((_BACKEND_DIR.parent / _candidate).resolve())
        else:
            MODEL_PATH = str((_BACKEND_DIR / _candidate).resolve())
    else:
        MODEL_PATH = str(_candidate.resolve())
else:
    MODEL_PATH = str((_BACKEND_DIR / "models" / "weights" / "densenet121_cxr.pt").resolve())

MODEL_WEIGHTS_DIR: str = os.getenv(
    "MODEL_WEIGHTS_DIR", str((_BACKEND_DIR / "models" / "weights").resolve())
)

# --- Medical disclaimer ---
MEDICAL_DISCLAIMER: str = (
    "AI-assisted screening/research prototype. "
    "Not a substitute for professional medical diagnosis."
)

