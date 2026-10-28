"""
Abstract base class for chest X-ray classification models.
Concrete implementations must provide load(), predict(), and explain().
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import numpy as np


@dataclass
class PredictionResult:
    """Output of a single inference pass."""
    label: str
    condition_id: str
    probability: float
    threshold: float
    detected: bool
    description: str
    anatomical_region: str
    clinical_significance: str


@dataclass
class InferenceOutput:
    """Full output bundle from an inference + explainability pass."""
    predictions: list[PredictionResult] = field(default_factory=list)
    inference_time_ms: float = 0.0
    model_name: str = ""
    model_version: str = ""
    is_demo: bool = False


class BaseChestXRayModel(ABC):
    """
    Interface every CXR model backend must satisfy.
    Keeps API routes model-agnostic.
    """

    @abstractmethod
    def load(self) -> None:
        """Load model weights into memory (called once at startup)."""
        ...

    @abstractmethod
    def predict(self, image: np.ndarray) -> InferenceOutput:
        """
        Run multi-label classification on a preprocessed image tensor.
        Args:
            image: numpy array of shape (1, 1, H, W), float32, normalised.
        Returns:
            InferenceOutput with per-pathology predictions.
        """
        ...

    @abstractmethod
    def explain(
        self,
        image: np.ndarray,
        condition_id: str,
        target_size: tuple[int, int] | None = None,
    ) -> dict:
        """
        Generate a Grad-CAM saliency map for a specific condition.
        Returns dict with heatmap_url (base64 data URL), target_layer, etc.
        """
        ...

    @abstractmethod
    def get_model_info(self) -> dict:
        """Return metadata about the loaded model."""
        ...
