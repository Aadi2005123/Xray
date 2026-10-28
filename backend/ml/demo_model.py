"""
Demo chest X-ray model implementation.
Provides simulated multi-label classification and explainability (Grad-CAM heatmaps)
when MODEL_MODE=demo or when no trained weights checkpoint exists.

Adheres strictly to BaseChestXRayModel interface.
Always flags outputs clearly as simulated / demo mode.
Reads from disease_labels.json as the single source of truth for the 10 classes.
"""

from __future__ import annotations
import os
import json
import time
import logging
from pathlib import Path
import numpy as np
import urllib.parse

from backend.ml.base_model import BaseChestXRayModel, InferenceOutput, PredictionResult

logger = logging.getLogger("backend.ml.demo")


def _load_canonical_conditions() -> list[dict]:
    """Load conditions from disease_labels.json, with safe fallback."""
    json_path = Path(__file__).resolve().parent / "disease_labels.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Error reading disease_labels.json: %s. Using built-in fallback.", e)

    # Built-in fallback ensuring 10 classes
    return [
        {"index": 0, "id": "atelectasis", "name": "Atelectasis", "nih_label": "Atelectasis", "anatomical_region": "Subsegmental / Lobar Lung Bases", "description": "Volume loss and collapse of alveolar units.", "clinical_significance": "Frequently post-operative or mucus plugging.", "default_threshold": 0.38, "focal_center": [240, 400, 95]},
        {"index": 1, "id": "cardiomegaly", "name": "Cardiomegaly", "nih_label": "Cardiomegaly", "anatomical_region": "Cardiac Silhouette / Mediastinum", "description": "Enlargement of cardiac silhouette >50% CTR.", "clinical_significance": "Associated with heart failure or cardiomyopathy.", "default_threshold": 0.45, "focal_center": [340, 340, 150]},
        {"index": 2, "id": "consolidation", "name": "Consolidation", "nih_label": "Consolidation", "anatomical_region": "Pulmonary Alveoli", "description": "Alveolar airspace opacification.", "clinical_significance": "Pneumonia, fluid, blood, or exudate.", "default_threshold": 0.40, "focal_center": [220, 310, 115]},
        {"index": 3, "id": "infiltration", "name": "Infiltration", "nih_label": "Infiltration", "anatomical_region": "Interstitium / Airspaces", "description": "Abnormal opacification within lung parenchyma.", "clinical_significance": "Broad infectious or inflammatory differential.", "default_threshold": 0.35, "focal_center": [230, 280, 120]},
        {"index": 4, "id": "mass", "name": "Mass", "nih_label": "Mass", "anatomical_region": "Pulmonary Fields / Mediastinum", "description": "Lesion >3 cm in diameter.", "clinical_significance": "Suspicious for primary or secondary neoplasm.", "default_threshold": 0.35, "focal_center": [380, 240, 90]},
        {"index": 5, "id": "nodule", "name": "Nodule", "nih_label": "Nodule", "anatomical_region": "Pulmonary Fields", "description": "Discrete rounded opacity <3 cm.", "clinical_significance": "Requires surveillance or Fleischner follow-up.", "default_threshold": 0.35, "focal_center": [210, 230, 60]},
        {"index": 6, "id": "pneumonia", "name": "Pneumonia", "nih_label": "Pneumonia", "anatomical_region": "Pulmonary Parenchyma (Lobes)", "description": "Infectious parenchymal consolidation.", "clinical_significance": "Requires acute clinical correlation and antibiotics.", "default_threshold": 0.40, "focal_center": [210, 330, 110]},
        {"index": 7, "id": "pneumothorax", "name": "Pneumothorax", "nih_label": "Pneumothorax", "anatomical_region": "Pleural Margin / Apex", "description": "Presence of air in pleural space.", "clinical_significance": "Potential acute emergency requiring decompression.", "default_threshold": 0.30, "focal_center": [450, 180, 90]},
        {"index": 8, "id": "pleural_effusion", "name": "Pleural Effusion", "nih_label": "Effusion", "anatomical_region": "Costophrenic Angles / Pleural Space", "description": "Fluid accumulation in pleural cavity.", "clinical_significance": "CHF, parapneumonic effusion, or malignancy.", "default_threshold": 0.35, "focal_center": [440, 440, 100]},
        {"index": 9, "id": "no_finding", "name": "No Finding", "nih_label": "No Finding", "anatomical_region": "Entire Thorax", "description": "Clear lung fields, normal cardiothoracic ratio.", "clinical_significance": "Unremarkable screening examination.", "default_threshold": 0.60, "focal_center": [300, 300, 130]},
    ]


DEMO_CONDITIONS = _load_canonical_conditions()


class DemoChestXRayModel(BaseChestXRayModel):
    """
    Simulation model for demonstration, integration testing, and local development.
    Produces deterministic outputs derived from image statistics.
    Never pretends to be real medical inference.
    """

    def __init__(self) -> None:
        self.is_loaded = False
        self.version = "1.0.0-demo"
        self.architecture = "DenseNet-121 (Demo Simulation Engine)"
        self.classes = DEMO_CONDITIONS
        self.class_names = [c["name"] for c in DEMO_CONDITIONS]

    def load(self) -> None:
        """Simulate loading model weights into memory."""
        self.is_loaded = True
        logger.info("DemoChestXRayModel loaded in simulation mode.")

    def predict(self, image: np.ndarray) -> InferenceOutput:
        """
        Produce simulated multi-label predictions derived purely from image statistics.
        Filenames have ZERO influence on the simulated prediction.
        """
        start_time = time.perf_counter()

        # Image-derived statistics (luminance mean, variance, quadrants) for deterministic results
        img_mean = float(np.mean(image))
        img_std = float(np.std(image))

        # Sub-quadrant statistics to reflect spatial luminance
        h, w = image.shape[-2], image.shape[-1]
        mid_h, mid_w = h // 2, w // 2
        top_left = float(np.mean(image[..., :mid_h, :mid_w]))
        top_right = float(np.mean(image[..., :mid_h, mid_w:]))
        bot_left = float(np.mean(image[..., mid_h:, :mid_w]))
        bot_right = float(np.mean(image[..., mid_h:, mid_w:]))

        predictions: list[PredictionResult] = []

        for i, cond in enumerate(self.classes):
            cid = cond["id"]
            threshold = cond.get("default_threshold", cond.get("threshold", 0.40))

            # Transparent pseudo-deterministic simulation based strictly on pixel content
            # Seed combines condition index, global image statistics, and quadrant deltas
            stat_signature = (
                (i + 1) * 31
                + int(abs(img_mean) * 1000)
                + int(abs(img_std) * 1000)
                + int(abs(top_left - bot_right) * 500)
                + int(abs(top_right - bot_left) * 500)
            )
            # Map into a calibrated demonstration probability between 0.05 and 0.92
            simulated_val = ((stat_signature % 87) + 5) / 100.0

            # Assign calibrated probability
            prob = round(min(0.95, max(0.05, simulated_val)), 3)
            detected = prob >= threshold

            predictions.append(
                PredictionResult(
                    label=cond["name"],
                    condition_id=cid,
                    probability=prob,
                    threshold=threshold,
                    detected=detected,
                    description=cond["description"],
                    anatomical_region=cond["anatomical_region"],
                    clinical_significance=cond.get("clinical_significance", ""),
                )
            )

        # Sort highest probability first
        predictions.sort(key=lambda x: x.probability, reverse=True)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return InferenceOutput(
            predictions=predictions,
            inference_time_ms=round(elapsed_ms, 2),
            model_name="DenseNet-121 (Demo Simulation Engine)",
            model_version=self.version,
            is_demo=True,
        )

    def explain(
        self,
        image: np.ndarray,
        condition_id: str,
        target_size: tuple[int, int] | None = None,
    ) -> dict:
        """
        Generate an anatomically aligned Grad-CAM saliency map for a condition.
        Returns a data URL containing an SVG Jet-gradient heatmap.
        """
        cond_data = next((c for c in self.classes if c["id"] == condition_id), None)
        if cond_data is None:
            cond_data = self.classes[0]

        cx, cy, r = cond_data.get("focal_center", [300, 300, 130])
        width, height = 600, 600

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <radialGradient id="jetGradient" cx="{(cx / width) * 100}%" cy="{(cy / height) * 100}%" r="{(r / width) * 100}%" fx="{(cx / width) * 100}%" fy="{(cy / height) * 100}%">
      <stop offset="0%" stop-color="#ef4444" stop-opacity="0.95"/>
      <stop offset="25%" stop-color="#f97316" stop-opacity="0.85"/>
      <stop offset="50%" stop-color="#eab308" stop-opacity="0.70"/>
      <stop offset="70%" stop-color="#22c55e" stop-opacity="0.45"/>
      <stop offset="88%" stop-color="#06b6d4" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.0"/>
    </radialGradient>
    <filter id="gradCamBlur">
      <feGaussianBlur stdDeviation="16"/>
    </filter>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#jetGradient)" filter="url(#gradCamBlur)"/>
</svg>"""

        encoded_svg = urllib.parse.quote(svg)
        data_url = f"data:image/svg+xml;utf8,{encoded_svg}"

        return {
            "conditionId": condition_id,
            "conditionName": cond_data["name"],
            "heatmapUrl": data_url,
            "overlayUrl": data_url,
            "maxActivationScore": 0.88,
            "targetLayer": "features.denseblock4.denselayer16.conv2 (Simulated)",
        }

    def get_model_info(self) -> dict:
        """Return metadata describing the demo model."""
        return {
            "name": "DenseNet-121 (Demo Simulation Engine)",
            "version": self.version,
            "architecture": self.architecture,
            "dataset": "NIH ChestX-ray14 (10-Class Subset Simulation)",
            "inputDimensions": "224 x 224 x 3 (Standardized Clinical CXR)",
            "benchmarkAurocMean": None,
            "benchmarkStatus": "Demo prototype mode — uncalibrated simulation",
            "lastUpdated": "2026-10-26",
            "supportedClasses": self.class_names,
        }
