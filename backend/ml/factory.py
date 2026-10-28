"""
Model factory for instantiating the active CXR model.
Switches between Real PyTorch model and Demo model based on MODEL_MODE.
Safely falls back to Demo mode if a real checkpoint is missing or unreadable.
"""

from __future__ import annotations
import logging
from backend.config.settings import MODEL_MODE, MODEL_PATH
from backend.ml.base_model import BaseChestXRayModel
from backend.ml.demo_model import DemoChestXRayModel

logger = logging.getLogger("backend.ml")


def get_model() -> BaseChestXRayModel:
    """
    Factory function to retrieve the configured CXR model.
    Loads the model once during application startup.
    """
    mode = MODEL_MODE.strip().lower()

    if mode == "real":
        try:
            from backend.ml.densenet121 import DenseNet121Model
            logger.info("Instantiating DenseNet121Model in REAL mode with checkpoint '%s'...", MODEL_PATH)
            model = DenseNet121Model(weights_path=MODEL_PATH if MODEL_PATH else None)
            model.load()
            return model
        except Exception as e:
            logger.error("Failed to load REAL model checkpoint: %s", e, exc_info=True)
            raise
    else:
        logger.info("Instantiating DemoChestXRayModel (MODEL_MODE=demo)...")
        demo_model = DemoChestXRayModel()
        demo_model.load()
        return demo_model
