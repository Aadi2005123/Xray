"""
Image preprocessing pipeline for chest X-ray inference.
Strictly matches canonical baseline preprocessing from preprocessing_config.json
and training transforms in dataset.py:
  1. Standard 3-channel RGB conversion for ImageNet backbone
  2. Resizing to (MODEL_INPUT_SIZE, MODEL_INPUT_SIZE)
  3. Float32 scaling to [0.0, 1.0]
  4. Standard ImageNet mean/std normalization
  5. Strictly NO CLAHE (as per baseline specification)
"""

import io
import numpy as np
from PIL import Image

from backend.config.settings import MODEL_INPUT_SIZE


def preprocess_cxr(raw_bytes: bytes) -> np.ndarray:
    """
    Convert raw image bytes into a preprocessed numpy array
    ready for model inference, mathematically matching training-time transforms.

    Returns:
        np.ndarray of shape (1, 3, H, W) — batch-of-one, 3-channel normalized float32 array.
    """
    # 1. Decode to 3-channel RGB (PIL)
    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")

    # 2. Resize to target input dimensions (224, 224)
    img_resized = img.resize((MODEL_INPUT_SIZE, MODEL_INPUT_SIZE), Image.Resampling.BILINEAR)

    # 3. Convert uint8 [0, 255] to float32 [0.0, 1.0]
    img_np = np.array(img_resized, dtype=np.float32) / 255.0  # (H, W, 3)

    # 4. Transpose to channel-first (3, H, W)
    img_chw = np.transpose(img_np, (2, 0, 1))

    # 5. Canonical ImageNet normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)[:, None, None]
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)[:, None, None]
    img_norm = (img_chw - mean) / std

    # 6. Add batch dimension -> (1, 3, H, W)
    return img_norm[np.newaxis, :, :, :]


def image_to_base64_data_url(raw_bytes: bytes, content_type: str = "image/png") -> str:
    """Convert raw image bytes to a base64 data URL for the frontend."""
    import base64
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:{content_type};base64,{b64}"

