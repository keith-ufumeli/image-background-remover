"""Core background-removal logic. The only module that imports rembg."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Literal

from PIL import Image
from rembg import new_session, remove

OutputFormat = Literal["png", "webp"]

SUPPORTED_INPUT_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


class UnsupportedFormatError(ValueError):
    """Raised when a file's extension is not a supported image format."""


def parse_hex_color(value: str) -> tuple[int, int, int]:
    """Parse a '#RRGGBB' (or 'RRGGBB') string into an (r, g, b) tuple."""
    stripped = value.lstrip("#")
    if len(stripped) != 6:
        raise ValueError(f"Color must be a hex string like '#RRGGBB', got {value!r}")
    try:
        return (
            int(stripped[0:2], 16),
            int(stripped[2:4], 16),
            int(stripped[4:6], 16),
        )
    except ValueError as exc:
        raise ValueError(f"Color must be a hex string like '#RRGGBB', got {value!r}") from exc


def _apply_background(
    image: Image.Image, bg_color: tuple[int, int, int] | None
) -> Image.Image:
    if bg_color is None:
        return image
    background = Image.new("RGB", image.size, bg_color)
    background.paste(image, mask=image.split()[3])
    return background


def _encode(image: Image.Image, output_format: OutputFormat) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=output_format.upper())
    return buffer.getvalue()


def _process(
    image: Image.Image,
    output_format: OutputFormat,
    bg_color: tuple[int, int, int] | None,
    session=None,
) -> bytes:
    result = remove(image, session=session)
    result = _apply_background(result, bg_color)
    return _encode(result, output_format)


def remove_background(
    input_path: Path,
    output_format: OutputFormat = "png",
    bg_color: tuple[int, int, int] | None = None,
    session=None,
) -> bytes:
    """Remove the background from a single image file and return encoded bytes."""
    if not input_path.is_file():
        raise FileNotFoundError(f"No such file: {input_path}")
    if input_path.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
        raise UnsupportedFormatError(f"Unsupported input format: {input_path.suffix!r}")
    image = Image.open(input_path)
    return _process(image, output_format, bg_color, session=session)


def remove_background_bytes(
    data: bytes,
    output_format: OutputFormat = "png",
    bg_color: tuple[int, int, int] | None = None,
) -> bytes:
    """Remove the background from in-memory image bytes (e.g. an HTTP upload)."""
    image = Image.open(io.BytesIO(data))
    return _process(image, output_format, bg_color)


def remove_background_batch(
    input_dir: Path,
    output_dir: Path,
    output_format: OutputFormat = "png",
    bg_color: tuple[int, int, int] | None = None,
) -> list[Path]:
    """Remove backgrounds from every supported image in input_dir.

    Reuses a single rembg session across the whole batch, since loading the
    model is the expensive part of each call.
    """
    if not input_dir.is_dir():
        raise NotADirectoryError(f"No such directory: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    session = new_session()
    written: list[Path] = []
    for candidate in sorted(input_dir.iterdir()):
        if candidate.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
            continue
        data = remove_background(candidate, output_format, bg_color, session=session)
        out_path = output_dir / f"{candidate.stem}.{output_format}"
        out_path.write_bytes(data)
        written.append(out_path)
    return written
