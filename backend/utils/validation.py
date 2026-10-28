"""
Upload validation utilities.
Validates file type, MIME, size, and image integrity.
Never trusts filenames. Never exposes filesystem paths.
"""

import io
import hashlib
from PIL import Image

from backend.config.settings import (
    MAX_UPLOAD_BYTES,
    ALLOWED_MIME_TYPES,
    ALLOWED_EXTENSIONS,
)

# Magic byte signatures for supported image formats
_MAGIC_BYTES: dict[str, bytes] = {
    "image/png": b"\x89PNG",
    "image/jpeg": b"\xff\xd8\xff",
    "image/webp": b"RIFF",
}


# Prevent decompression bombs (pixel-flood DoS)
Image.MAX_IMAGE_PIXELS = 16_000_000
MAX_IMAGE_DIMENSION = 4096


class ValidationError(Exception):
    """Raised when uploaded file fails safety checks."""
    pass


def validate_upload(
    content: bytes,
    content_type: str | None,
    filename: str | None,
) -> None:
    """
    Multi-layer upload validation.
    Raises ValidationError with a safe user-facing message on failure.
    """
    # 1) Size
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValidationError(
            f"File exceeds maximum allowed size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
        )

    if len(content) == 0:
        raise ValidationError("Uploaded file is empty.")

    # 2) Extension (informational; never trusted alone)
    if filename:
        ext = _safe_extension(filename)
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"File extension '{ext}' is not supported. "
                f"Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            )

    # 3) MIME type from the client header
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"MIME type '{content_type}' is not supported. "
            f"Accepted: {', '.join(sorted(ALLOWED_MIME_TYPES))}."
        )

    # 4) Magic-byte verification (prevents polyglot file attacks)
    if not _check_magic_bytes(content):
        raise ValidationError(
            "File header does not match any supported image format. "
            "The file may be corrupted or not a valid image."
        )

    # 5) Image integrity and dimension limits via Pillow
    try:
        img = Image.open(io.BytesIO(content))
        img.verify()  # checks for truncation / corruption
        # Re-check dimensions (some corruptions occur with huge header-declared bounds)
        w, h = img.size
        if w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
            raise ValidationError(
                f"Image dimensions ({w}x{h}) exceed maximum permitted resolution of {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}."
            )
    except ValidationError:
        raise
    except Exception:
        raise ValidationError(
            "Image could not be decoded. The file may be corrupted or incomplete."
        )


def compute_sha256(content: bytes) -> str:
    """Returns the hex SHA-256 digest of raw file bytes."""
    return hashlib.sha256(content).hexdigest()


def _safe_extension(filename: str) -> str:
    """Extract lowercase extension from filename. Never used for path construction."""
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()


def _check_magic_bytes(content: bytes) -> bool:
    """Return True if the content starts with a known image magic signature."""
    for sig in _MAGIC_BYTES.values():
        if content[: len(sig)] == sig:
            return True
    return False
