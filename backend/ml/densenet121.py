"""
PyTorch DenseNet-121 Model Wrapper with integrated Grad-CAM explainability.
Used when MODEL_MODE=real.
Requires a trained .pt model checkpoint to operate.
Reads target classes from disease_labels.json.
"""

from __future__ import annotations
import os
import json
import base64
import logging
from pathlib import Path
import numpy as np
import cv2

from backend.ml.base_model import BaseChestXRayModel, InferenceOutput, PredictionResult

logger = logging.getLogger("backend.ml.densenet")


def _load_classes() -> list[dict]:
    """Load canonical classes from disease_labels.json."""
    json_path = Path(__file__).resolve().parent / "disease_labels.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


class DenseNet121Model(BaseChestXRayModel):
    """
    Torch-based DenseNet-121 architecture for chest X-ray disease classification.
    Supports feature extraction from the final dense block and Grad-CAM backpropagation.
    """

    def __init__(self, weights_path: str | None = None) -> None:
        self.weights_path = weights_path
        self.is_loaded = False
        self.model = None
        self.device = "cpu"
        self.version = "1.0.0-pytorch"
        self.architecture = "DenseNet-121 (Multi-Label Sigmoid Classifier)"
        self.classes = _load_classes()
        self.class_names = [c["name"] for c in self.classes]

    def _resolve_weights_path(self) -> Path:
        """Resolve model checkpoint path or raise FileNotFoundError if unavailable."""
        if self.weights_path:
            p = Path(self.weights_path)
            if p.exists():
                return p
            raise FileNotFoundError(
                f"Configured model checkpoint not found at: '{self.weights_path}'. "
                "Please verify the file path or ensure MODEL_PATH points to a valid .pt checkpoint."
            )

        # Look in standard default locations
        default_locations = [
            Path(__file__).resolve().parent.parent / "models" / "weights" / "densenet121_cxr.pt",
            Path("backend/models/weights/densenet121_cxr.pt"),
            Path("models/weights/densenet121_cxr.pt"),
        ]
        for loc in default_locations:
            if loc.exists():
                return loc

        raise FileNotFoundError(
            "Trained DenseNet-121 weights checkpoint not found in default locations. "
            "Real ML inference requires a trained model checkpoint (.pt). "
            "Please ensure densenet121_cxr.pt exists under backend/models/weights/."
        )

    def load(self) -> None:
        """Load PyTorch DenseNet model and checkpoint weights."""
        try:
            import torch
            import torch.nn as nn
            import torchvision.models as models

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Initializing DenseNet-121 on %s", self.device)

            resolved_path = self._resolve_weights_path()
            logger.info("Found pre-trained checkpoint at: %s", resolved_path)

            # Build backbone architecture
            self.model = models.densenet121(weights=None)
            num_classes = len(self.classes) if self.classes else 10
            in_features = self.model.classifier.in_features
            self.model.classifier = nn.Linear(in_features, num_classes)

            # Load trained checkpoint state
            state_dict = torch.load(resolved_path, map_location=self.device)
            if "model_state_dict" in state_dict:
                state_dict = state_dict["model_state_dict"]
            self.model.load_state_dict(state_dict)

            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            logger.info("DenseNet-121 loaded successfully with trained weights (%d classes).", num_classes)
        except Exception as e:
            logger.error("Failed to initialize PyTorch model: %s", e)
            raise

    def predict(self, image: np.ndarray) -> InferenceOutput:
        """Execute forward pass and compute multi-label probabilities."""
        import time
        start_time = time.perf_counter()
        import torch

        # Prepare 3-channel tensor if needed by ImageNet backbone
        # image shape: (1, 1, 224, 224) or (1, 3, 224, 224)
        if image.shape[1] == 1:
            tensor_3ch = np.repeat(image, 3, axis=1)
        else:
            tensor_3ch = image

        t_input = torch.from_numpy(tensor_3ch).float().to(self.device)

        with torch.no_grad():
            logits = self.model(t_input)
            probs = torch.sigmoid(logits).cpu().numpy()[0]

        predictions: list[PredictionResult] = []
        for i, cond in enumerate(self.classes):
            prob = float(probs[i]) if i < len(probs) else 0.05
            thresh = cond.get("default_threshold", cond.get("threshold", 0.40))
            predictions.append(
                PredictionResult(
                    label=cond["name"],
                    condition_id=cond["id"],
                    probability=round(prob, 3),
                    threshold=thresh,
                    detected=prob >= thresh,
                    description=cond["description"],
                    anatomical_region=cond["anatomical_region"],
                    clinical_significance=cond.get("clinical_significance", ""),
                )
            )

        predictions.sort(key=lambda x: x.probability, reverse=True)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return InferenceOutput(
            predictions=predictions,
            inference_time_ms=round(elapsed_ms, 2),
            model_name="DenseNet-121 (Trained Checkpoint)",
            model_version=self.version,
            is_demo=False,
        )

    def explain(
        self,
        image: np.ndarray,
        condition_id: str,
        target_size: tuple[int, int] | None = None,
    ) -> dict:
        """
        Generate authentic Grad-CAM saliency map for the selected condition.
        Uses gradient backpropagation into the final dense block.
        Produces an RGBA PNG with transparent background outside activation zones,
        avoiding whole-image blue tinting.
        Optionally resizes to target_size (width, height) to match input image aspect ratio.
        """
        import torch

        cond_data = next((c for c in self.classes if c["id"] == condition_id), None)
        if cond_data is None:
            cond_data = self.classes[0]
            condition_id = cond_data["id"]

        class_idx = next((i for i, c in enumerate(self.classes) if c["id"] == condition_id), 0)

        # Prepare 3-channel tensor
        if image.shape[1] == 1:
            tensor_3ch = np.repeat(image, 3, axis=1)
        else:
            tensor_3ch = image

        activations = None
        gradients = None

        def forward_hook(module, input, output):
            nonlocal activations
            activations = output

        def backward_hook(module, grad_in, grad_out):
            nonlocal gradients
            gradients = grad_out[0]

        target_layer = self.model.features.denseblock4.denselayer16.conv2
        fwd_handle = target_layer.register_forward_hook(forward_hook)
        bwd_handle = target_layer.register_full_backward_hook(backward_hook)

        try:
            t_input = torch.from_numpy(tensor_3ch).float().to(self.device)
            t_input.requires_grad = True

            with torch.enable_grad():
                self.model.zero_grad()
                logits = self.model(t_input)
                score = logits[0, class_idx]
                score.backward()

            if gradients is None or activations is None:
                raise RuntimeError("Failed to capture feature gradients or activations for Grad-CAM.")

            # Global average pooling of gradients
            grad_np = gradients.detach().cpu().numpy()[0]       # (C, H, W)
            act_np = activations.detach().cpu().numpy()[0]       # (C, H, W)

            # Check finiteness of captured feature tensors
            is_finite = bool(np.all(np.isfinite(grad_np)) and np.all(np.isfinite(act_np)))
            if not is_finite:
                logger.warning("Non-finite values encountered in Grad-CAM gradients or activations; zeroing invalid elements.")
                grad_np = np.nan_to_num(grad_np, nan=0.0, posinf=0.0, neginf=0.0)
                act_np = np.nan_to_num(act_np, nan=0.0, posinf=0.0, neginf=0.0)

            weights = np.mean(grad_np, axis=(1, 2))              # (C,)
            cam = np.zeros(act_np.shape[1:], dtype=np.float32)   # (H, W)

            for i, w in enumerate(weights):
                cam += w * act_np[i]

            # Apply ReLU: only positive contributions to class activation
            cam = np.maximum(cam, 0)
            
            # Extract raw pre-normalization statistics (after ReLU)
            raw_peak = float(np.max(cam))
            raw_min = float(np.min(cam))
            raw_mean = float(np.mean(cam))
            is_degenerate = bool((raw_peak - raw_min) < 1e-8)

            # Weak activation handling:
            # Baseline reference threshold for DenseNet-121 final convolutional features.
            # Documented rationale: Confident disease features typically produce raw peaks in [0.05, 0.20+].
            # Activations with raw peak < 0.02 represent diffuse baseline gradient flow without localized salience.
            # Configurable via environment variable GRADCAM_WEAK_THRESHOLD (default: 0.02).
            weak_threshold = float(os.getenv("GRADCAM_WEAK_THRESHOLD", "0.02"))
            is_weak = bool(raw_peak < weak_threshold)

            # Safe normalization:
            # Separate raw statistics from visualization scaling.
            # Safely avoid division by zero on degenerate or near-zero maps.
            if is_degenerate or raw_peak < 1e-8:
                cam_norm = np.zeros_like(cam)
            else:
                cam_norm = (cam - raw_min) / (raw_peak - raw_min)

            # Resolve output dimensions (match original radiograph aspect ratio if provided)
            out_w, out_h = target_size if (target_size and len(target_size) == 2) else (600, 600)

            # Resize to output resolution
            cam_resized = cv2.resize(cam_norm, (out_w, out_h), interpolation=cv2.INTER_CUBIC)
            cam_resized = np.clip(cam_resized, 0.0, 1.0)

            # Apply colormap (cv2.COLORMAP_JET) -> BGR
            heatmap_norm = np.uint8(255 * cam_resized)
            heatmap_bgr = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
            heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)

            # Construct transparent RGBA overlay:
            # Low activation (< 0.12) is 100% transparent (no blue wash)
            # Attenuation factor: If activation is weak (raw_peak < weak_threshold), proportionally attenuate
            # the alpha channel (clamped in [0.0, 1.0]) so weak activations are NOT rendered as saturated, high-opacity overlays.
            # If raw_peak is 0, attenuation is 0.0 (completely transparent).
            # This maintains relative morphology for exploration while visually communicating low confidence.
            # Note: Grad-CAM raw magnitude reflects gradient attribution, NOT calibrated disease probability.
            if weak_threshold > 1e-8:
                attenuation = float(np.clip(raw_peak / weak_threshold, 0.0, 1.0))
            else:
                attenuation = 1.0

            alpha_mask = np.clip((cam_resized - 0.12) / 0.88, 0.0, 1.0)
            alpha_channel = np.uint8(alpha_mask * 230.0 * attenuation)

            heatmap_rgba = np.dstack([heatmap_rgb, alpha_channel])

            # Encode RGBA PNG
            success, png_rgba_buf = cv2.imencode(".png", cv2.cvtColor(heatmap_rgba, cv2.COLOR_RGBA2BGRA))
            if not success:
                raise RuntimeError("Failed to encode Grad-CAM PNG buffer.")

            b64_str = base64.b64encode(png_rgba_buf).decode("ascii")
            heatmap_url = f"data:image/png;base64,{b64_str}"

            # Create composite blended overlay
            # Denormalize input image to grayscale [0, 255] for backdrop
            base_ch = tensor_3ch[0, 0]
            base_denorm = np.clip((base_ch * 0.229 + 0.485) * 255.0, 0, 255).astype(np.uint8)
            base_resized = cv2.resize(base_denorm, (out_w, out_h))
            base_rgb = cv2.cvtColor(base_resized, cv2.COLOR_GRAY2RGB)

            alpha_f = (alpha_channel.astype(np.float32) / 255.0)[:, :, None]
            composite_rgb = np.uint8(base_rgb * (1.0 - alpha_f * 0.7) + heatmap_rgb * (alpha_f * 0.7))

            _, composite_buf = cv2.imencode(".png", cv2.cvtColor(composite_rgb, cv2.COLOR_RGB2BGR))
            overlay_b64 = base64.b64encode(composite_buf).decode("ascii")
            overlay_url = f"data:image/png;base64,{overlay_b64}"

            return {
                "conditionId": condition_id,
                "conditionName": cond_data["name"],
                "heatmapUrl": heatmap_url,
                "overlayUrl": overlay_url,
                "maxActivationScore": round(raw_peak, 3),
                "rawPeak": round(raw_peak, 6),
                "rawMean": round(raw_mean, 6),
                "isFinite": is_finite,
                "isWeakActivation": is_weak,
                "targetLayer": "features.denseblock4.denselayer16.conv2",
            }
        except Exception as e:
            logger.error("Grad-CAM generation error for %s: %s", condition_id, e, exc_info=True)
            raise
        finally:
            fwd_handle.remove()
            bwd_handle.remove()
            self.model.zero_grad()

    def get_model_info(self) -> dict:
        """Return verified metadata about the loaded DenseNet-121 model."""
        return {
            "name": "DenseNet-121 Clinical Backbone",
            "version": self.version,
            "architecture": self.architecture,
            "dataset": "NIH ChestX-ray14 10-Class Subset",
            "inputDimensions": "224 x 224 x 3 (Standardized CXR RGB)",
            "benchmarkAurocMean": None,  # External literature claims 0.842 unverified on local weights
            "benchmarkStatus": "Literature reference (0.842) unverified; local training reported epoch 5 val AUROC: 0.7890, test AUROC: 0.7793",
            "lastUpdated": "2026-10-26",
            "supportedClasses": self.class_names,
        }

