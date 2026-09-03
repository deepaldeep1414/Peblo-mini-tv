import random
from io import BytesIO

import pytest
from PIL import Image

from app.services.artwork_validation import validate_and_probe, ArtworkValidationError


def _make_jpeg(width, height, quality=85) -> bytes:
    img = Image.new("RGB", (width, height), color=(120, 140, 160))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _make_noisy_jpeg(width, height, quality=100) -> bytes:
    # Random-noise pixels compress far worse than a flat color, so this
    # reliably produces a file over the 200KB ceiling for the "too big" test.
    random.seed(42)
    pixels = bytes(random.getrandbits(8) for _ in range(width * height * 3))
    img = Image.frombytes("RGB", (width, height), pixels)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def test_valid_poster_passes():
    data = _make_jpeg(600, 900)
    w, h = validate_and_probe("poster", data)
    assert (w, h) == (600, 900)


def test_wrong_aspect_ratio_rejected():
    data = _make_jpeg(600, 600)  # 1:1, not 2:3
    with pytest.raises(ArtworkValidationError):
        validate_and_probe("poster", data)


def test_oversized_file_rejected():
    data = _make_noisy_jpeg(900, 1350, quality=100)
    with pytest.raises(ArtworkValidationError):
        validate_and_probe("poster", data)


def test_unknown_kind_rejected():
    data = _make_jpeg(600, 900)
    with pytest.raises(ArtworkValidationError):
        validate_and_probe("hero", data)
