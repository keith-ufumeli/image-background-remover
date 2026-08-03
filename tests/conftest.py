from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def sample_image_path(tmp_path: Path) -> Path:
    """A small synthetic JPEG: a red square on a blue background."""
    image = Image.new("RGB", (64, 64), (30, 30, 200))
    for x in range(16, 48):
        for y in range(16, 48):
            image.putpixel((x, y), (200, 30, 30))
    path = tmp_path / "sample.jpg"
    image.save(path)
    return path
