"""
Machine Learning and Computer Vision package.
Provides modular model architectures, inference pipelines, and evaluation metrics.
"""

from backend.ml.base_model import BaseChestXRayModel, InferenceOutput, PredictionResult
from backend.ml.demo_model import DemoChestXRayModel, DEMO_CONDITIONS
from backend.ml.factory import get_model
from backend.ml.evaluation import compute_multilabel_metrics
from backend.ml.dataset import ChestXRayDataset, HuggingFaceChestXRayDataset

__all__ = [
    "BaseChestXRayModel",
    "InferenceOutput",
    "PredictionResult",
    "DemoChestXRayModel",
    "DEMO_CONDITIONS",
    "get_model",
    "compute_multilabel_metrics",
    "ChestXRayDataset",
    "HuggingFaceChestXRayDataset",
]
