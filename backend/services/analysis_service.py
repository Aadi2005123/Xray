"""
Analysis Service layer.
Coordinates validation, preprocessing, model inference, and response assembly.
Keeps ML logic completely decoupled from HTTP API routes.
"""

from __future__ import annotations
import uuid
import time
from datetime import datetime, timezone
import numpy as np

from backend.ml.base_model import BaseChestXRayModel
from backend.utils.validation import validate_upload, compute_sha256
from backend.utils.preprocessing import preprocess_cxr, image_to_base64_data_url
from backend.schemas.analysis import (
    AnalysisResultResponse,
    PathologyPredictionSchema,
    HeatmapDataSchema,
    ExplainRequest,
    ReportRequest,
    ReportResponse,
    ClinicalInterpretationResponse,
    InterpretRequest,
)
from backend.services.interpretation_service import interpretation_service


def _get_severity(probability: float, threshold: float) -> str:
    """Classify risk category matching clinical threshold standards."""
    if probability < threshold:
        return "low"
    if probability < threshold + 0.20:
        return "moderate"
    return "high"


class AnalysisService:
    """
    Business and orchestration logic for chest X-ray processing.
    """

    def __init__(self, model: BaseChestXRayModel) -> None:
        self.model = model
        self._image_cache: dict[str, np.ndarray] = {}
        self._predictions_cache: dict[str, list[PathologyPredictionSchema]] = {}
        self._dimensions_cache: dict[str, tuple[int, int]] = {}
        self._max_cache_entries = 50

    def _cache_session(
        self,
        analysis_id: str,
        image_tensor: np.ndarray,
        predictions: list[PathologyPredictionSchema],
        dimensions: tuple[int, int],
    ) -> None:
        """Cache image tensor, predictions, and dimensions in memory for targeted lookups."""
        if len(self._image_cache) >= self._max_cache_entries:
            oldest_key = next(iter(self._image_cache))
            del self._image_cache[oldest_key]
            self._predictions_cache.pop(oldest_key, None)
            self._dimensions_cache.pop(oldest_key, None)
        self._image_cache[analysis_id] = image_tensor
        self._predictions_cache[analysis_id] = predictions
        self._dimensions_cache[analysis_id] = dimensions

    def analyze_image(
        self,
        raw_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> AnalysisResultResponse:
        """
        Full end-to-end pipeline:
        1. Validation (size, extension, mime, magic bytes, Pillow decode)
        2. Hashing (SHA-256 for audit trail)
        3. Preprocessing (Grayscale, Resize 224x224, CLAHE, Normalize)
        4. Model Inference (Multi-label probabilities)
        5. Grad-CAM Explainability (Saliency maps for detected pathologies)
        6. Summary generation and response formatting
        """
        start_time = time.perf_counter()

        # Step 1: Validation
        validate_upload(raw_bytes, content_type, filename)

        # Step 2: Hashing
        sha256_hash = compute_sha256(raw_bytes)

        # Step 3: Preprocessing
        image_tensor = preprocess_cxr(raw_bytes)

        # Extract image dimensions safely using Pillow
        from PIL import Image
        import io
        pil_img = Image.open(io.BytesIO(raw_bytes))
        width, height = pil_img.size

        # Step 4: Model Inference (purely image-derived, filenames have zero influence)
        if hasattr(self.model, "predict"):
            inference_out = self.model.predict(image_tensor)
        else:
            raise RuntimeError("Model does not implement predict()")

        # Step 5: Format predictions
        predictions: list[PathologyPredictionSchema] = []
        heatmaps: dict[str, HeatmapDataSchema] = {}

        for p in inference_out.predictions:
            pred_schema = PathologyPredictionSchema(
                id=p.condition_id,
                name=p.label,
                probability=p.probability,
                severity=_get_severity(p.probability, p.threshold),
                threshold=p.threshold,
                detected=p.detected,
                description=p.description,
                anatomical_region=p.anatomical_region,
                clinical_significance=p.clinical_significance,
            )
            predictions.append(pred_schema)

            # Generate explainability heatmap for each pathology (aligned to original dimensions)
            explain_dict = self.model.explain(image_tensor, p.condition_id, target_size=(width, height))
            heatmaps[p.condition_id] = HeatmapDataSchema(
                condition_id=explain_dict["conditionId"],
                condition_name=explain_dict["conditionName"],
                heatmap_url=explain_dict["heatmapUrl"],
                overlay_url=explain_dict["overlayUrl"],
                max_activation_score=explain_dict["maxActivationScore"],
                raw_peak=explain_dict.get("rawPeak"),
                raw_mean=explain_dict.get("rawMean"),
                is_finite=explain_dict.get("isFinite", True),
                is_weak_activation=explain_dict.get("isWeakActivation", False),
                target_layer=explain_dict["targetLayer"],
            )

        # Order predictions descending by probability
        predictions.sort(key=lambda x: x.probability, reverse=True)

        # Identify all detected disease pathologies (excluding no_finding/normal)
        detected_pathologies = [
            p for p in predictions if p.detected and p.id not in ("no_finding", "normal")
        ]
        no_finding_pred = next((p for p in predictions if p.id == "no_finding"), None)

        # Build clinical summary & select primary top finding
        if detected_pathologies:
            primary_finding = detected_pathologies[0]
            top_finding = primary_finding
            other_detected = [p.name for p in detected_pathologies[1:]]
            secondary_text = f" Secondary activations above threshold: {', '.join(other_detected)}." if other_detected else ""
            summary = (
                f"Primary model activation detected for {primary_finding.name} "
                f"(uncalibrated score: {primary_finding.probability * 100:.1f}%, screening threshold: {primary_finding.threshold * 100:.0f}%). "
                f"Target anatomical region: {primary_finding.anatomical_region}. "
                f"Morphological finding requires clinical correlation.{secondary_text}"
            )
        else:
            top_finding = predictions[0] if predictions else None
            if no_finding_pred and no_finding_pred.detected:
                summary = (
                    f"No targeted thoracic findings detected above screening thresholds "
                    f"(No Finding score: {no_finding_pred.probability * 100:.1f}%, threshold: {no_finding_pred.threshold * 100:.0f}%). "
                    "Note: Sub-threshold findings do not establish absence of disease or normal anatomy; "
                    "sub-radiographic lesions, early malignancies, or non-targeted abnormalities cannot be excluded on standard radiographs alone."
                )
            else:
                nf_score_text = f" (No Finding score: {no_finding_pred.probability * 100:.1f}%, threshold: {no_finding_pred.threshold * 100:.0f}%)" if no_finding_pred else ""
                summary = (
                    f"No targeted thoracic findings detected above screening thresholds; "
                    f"model activations across all categories remain indeterminate or sub-threshold{nf_score_text}. "
                    "Note: Sub-threshold findings do not establish absence of disease or normal anatomy; "
                    "sub-radiographic lesions, early malignancies, or non-targeted abnormalities cannot be excluded on standard radiographs alone."
                )

        if inference_out.is_demo:
            summary += " [Demo Mode — simulated output]"

        # Original image as data URL for frontend viewer
        data_url = image_to_base64_data_url(raw_bytes, content_type or "image/png")

        analysis_id = f"CXR-{uuid.uuid4().hex[:7].upper()}"
        self._cache_session(analysis_id, image_tensor, predictions, (width, height))

        # Generate finding-based clinical interpretation
        finding_interpretation = interpretation_service.interpret_findings(predictions)

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return AnalysisResultResponse(
            analysis_id=analysis_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            original_image=data_url,
            file_name=filename,
            file_size_bytes=len(raw_bytes),
            image_dimensions={"width": width, "height": height},
            image_hash_sha256=sha256_hash,
            execution_time_ms=round(total_elapsed_ms, 2),
            predictions=predictions,
            top_finding=top_finding,
            heatmaps=heatmaps,
            clinical_summary=summary,
            is_simulated_fallback=inference_out.is_demo,
            finding_interpretation=finding_interpretation,
        )

    def explain_condition(self, req: ExplainRequest) -> HeatmapDataSchema:
        """
        Generate targeted Grad-CAM explanation for a specific condition on the active radiograph.
        """
        image_tensor = self._image_cache.get(req.analysis_id)
        if image_tensor is None:
            raise ValueError(
                f"Analysis session '{req.analysis_id}' not found in active in-memory cache. "
                "Please run radiograph analysis before requesting targeted Grad-CAM."
            )

        valid_ids = [c["id"] for c in getattr(self.model, "classes", [])]
        if valid_ids and req.condition_id not in valid_ids:
            raise ValueError(
                f"Unknown condition ID '{req.condition_id}'. "
                f"Supported conditions: {', '.join(valid_ids)}"
            )

        target_size = self._dimensions_cache.get(req.analysis_id)
        explain_dict = self.model.explain(image_tensor, req.condition_id, target_size=target_size)

        return HeatmapDataSchema(
            condition_id=explain_dict["conditionId"],
            condition_name=explain_dict["conditionName"],
            heatmap_url=explain_dict["heatmapUrl"],
            overlay_url=explain_dict["overlayUrl"],
            max_activation_score=explain_dict["maxActivationScore"],
            raw_peak=explain_dict.get("rawPeak"),
            raw_mean=explain_dict.get("rawMean"),
            is_finite=explain_dict.get("isFinite", True),
            is_weak_activation=explain_dict.get("isWeakActivation", False),
            target_layer=explain_dict["targetLayer"],
        )

    def interpret_session(self, req: InterpretRequest) -> ClinicalInterpretationResponse:
        """
        Generate finding-based clinical interpretations for an active analysis session.
        """
        predictions = self._predictions_cache.get(req.analysis_id)
        if predictions is None:
            raise ValueError(
                f"Analysis session '{req.analysis_id}' not found in active session cache. "
                "Please run radiograph analysis before requesting finding interpretation."
            )
        return interpretation_service.interpret_findings(predictions)

    def generate_report(self, req: ReportRequest) -> ReportResponse:
        """
        Generate or register structured clinical consultation report.
        """
        # Return success confirmation with study linkage
        return ReportResponse(
            success=True,
            report_url=f"/reports/{req.study_id}.pdf" if req.study_id else None,
        )
