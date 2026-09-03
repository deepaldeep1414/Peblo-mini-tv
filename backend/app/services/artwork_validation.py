"""
Validates uploaded artwork against reference.json-style specs, returning
editor-actionable error messages (not stack traces / technical jargon --
per the challenge's "non-technical editor can act on it" requirement).
"""
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from app.core.config import get_settings

settings = get_settings()


@dataclass
class ArtworkValidationError(Exception):
    message: str

    def __str__(self):
        return self.message


def validate_and_probe(kind: str, data: bytes) -> tuple[int, int]:
    """Returns (width, height) or raises ArtworkValidationError with a
    plain-English message."""
    if kind not in settings.ARTWORK_SPECS:
        raise ArtworkValidationError(
            f"Unknown artwork type '{kind}'. Must be one of: poster, banner, thumbnail."
        )

    spec = settings.ARTWORK_SPECS[kind]

    if len(data) > settings.ARTWORK_MAX_BYTES:
        kb = len(data) / 1024
        raise ArtworkValidationError(
            f"This {kind} image is {kb:.0f} KB, which is over the 200 KB limit. "
            f"Please compress or resize it and try again."
        )

    try:
        img = Image.open(BytesIO(data))
        img.verify()
        # re-open after verify() (verify() leaves the file unusable for further reads)
        img = Image.open(BytesIO(data))
        width, height = img.size
    except Exception:
        raise ArtworkValidationError(
            "This file doesn't look like a valid image. Please upload a JPG or PNG."
        )

    ratio_w, ratio_h = spec["ratio"]
    expected_ratio = ratio_w / ratio_h
    actual_ratio = width / height
    tolerance = settings.ARTWORK_RATIO_TOLERANCE
    if abs(actual_ratio - expected_ratio) / expected_ratio > tolerance:
        raise ArtworkValidationError(
            f"This {kind} image is {width}x{height} ({actual_ratio:.2f}:1), but we need "
            f"a {ratio_w}:{ratio_h} image close to {spec['target'][0]}x{spec['target'][1]}. "
            f"Please crop it to the right shape and re-upload."
        )

    return width, height
