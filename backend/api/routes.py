"""
API router definitions.
All endpoints delegate to the service layer.
No ML code or model imports live inside this file.
"""

from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Request
from fastapi.responses import JSONResponse

from backend.schemas.analysis import (
    HealthResponse,
    ModelInfoResponse,
    AnalysisResultResponse,
    ExplainRequest,
    HeatmapDataSchema,
    ReportRequest,
    ReportResponse,
    ErrorResponse,
    InterpretRequest,
    ClinicalInterpretationResponse,
)
from backend.services.analysis_service import AnalysisService
from backend.utils.validation import ValidationError

logger = logging.getLogger("backend.api")

router = APIRouter(prefix="/api", tags=["chest-xray-ai"])


def get_analysis_service(request: Request) -> AnalysisService:
    """Dependency injection to provide the singleton AnalysisService."""
    return request.app.state.analysis_service


# ── GET /api/health ──────────────────────────────────────────────────
@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check & Model Readiness",
)
async def check_health(
    request: Request,
    service: AnalysisService = Depends(get_analysis_service),
) -> HealthResponse:
    """Return backend server status and whether the CXR model is loaded in memory."""
    is_loaded = getattr(service.model, "is_loaded", True)
    return HealthResponse(
        status="ok",
        version="1.0.0",
        device="cpu",
        model_loaded=is_loaded,
    )


# ── GET /api/model-info ──────────────────────────────────────────────
@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Retrieve Deep Learning Architecture & Benchmarks",
)
async def get_model_info(
    service: AnalysisService = Depends(get_analysis_service),
) -> ModelInfoResponse:
    """Return architecture specifications, training dataset origins, and AUROC benchmarks."""
    info_dict = service.model.get_model_info()
    return ModelInfoResponse(**info_dict)


# ── POST /api/analyze ────────────────────────────────────────────────
@router.post(
    "/analyze",
    response_model=AnalysisResultResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation failure or corrupted file"},
        500: {"model": ErrorResponse, "description": "Internal analysis error"},
    },
    summary="Upload & Analyze Chest Radiograph",
)
async def analyze_xray(
    file: UploadFile = File(..., description="Chest X-Ray image file (PNG, JPEG, WebP)"),
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisResultResponse:
    """
    Stream upload, validate against strict security criteria, preprocess with CLAHE,
    execute multi-label deep learning classification, and compute Grad-CAM heatmaps.
    Uploaded image is processed in memory and never permanently stored.
    """
    try:
        raw_bytes = await file.read()
        return service.analyze_image(
            raw_bytes=raw_bytes,
            filename=file.filename or "uploaded_xray.png",
            content_type=file.content_type or "image/png",
        )
    except ValidationError as ve:
        logger.warning("Upload validation failed: %s", ve)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error("Analysis pipeline error: %s", e, exc_info=True)
        # Controlled error message without exposing stack traces
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference pipeline encountered an unexpected error. Please verify the radiograph and retry.",
        )


# ── POST /api/explain ────────────────────────────────────────────────
@router.post(
    "/explain",
    response_model=HeatmapDataSchema,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid condition ID"},
    },
    summary="Generate Targeted Grad-CAM Saliency Explanation",
)
async def explain_condition(
    req: ExplainRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> HeatmapDataSchema:
    """Generate high-resolution Grad-CAM saliency map for a specific thoracic condition."""
    try:
        return service.explain_condition(req)
    except ValueError as ve:
        logger.warning("Explain condition error: %s", ve)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error("Explain error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate explainability saliency map.",
        )


# ── POST /api/interpret ──────────────────────────────────────────────
@router.post(
    "/interpret",
    response_model=ClinicalInterpretationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid analysis session ID"},
    },
    summary="Retrieve Finding-Based Clinical Interpretation & Differential Associations",
)
async def interpret_findings(
    req: InterpretRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> ClinicalInterpretationResponse:
    """Map detected model findings to documented possible clinical conditions and limitations."""
    try:
        return service.interpret_session(req)
    except ValueError as ve:
        logger.warning("Interpret session error: %s", ve)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error("Interpretation error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate clinical finding interpretations.",
        )


# ── POST /api/report ─────────────────────────────────────────────────
@router.post(
    "/report",
    response_model=ReportResponse,
    summary="Export Structured Clinical Consultation Report",
)
async def generate_report(
    req: ReportRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> ReportResponse:
    """Generate structured audit/consultation report payload for archiving or printing."""
    try:
        return service.generate_report(req)
    except Exception as e:
        logger.error("Report generation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report compilation failed.",
        )
