from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from bgremover.core import (
    UnsupportedFormatError,
    parse_hex_color,
    remove_background,
    remove_background_batch,
    remove_background_bytes,
)


def test_parse_hex_color():
    assert parse_hex_color("#FFFFFF") == (255, 255, 255)
    assert parse_hex_color("00ff80") == (0, 255, 128)


def test_parse_hex_color_rejects_bad_input():
    with pytest.raises(ValueError):
        parse_hex_color("#FFF")


def test_remove_background_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        remove_background(tmp_path / "does_not_exist.jpg")


def test_remove_background_unsupported_extension(tmp_path: Path):
    bad_file = tmp_path / "notes.txt"
    bad_file.write_text("hello")
    with pytest.raises(UnsupportedFormatError):
        remove_background(bad_file)


def test_remove_background_default_is_transparent(sample_image_path: Path):
    data = remove_background(sample_image_path)
    result = Image.open(io.BytesIO(data))
    assert result.mode == "RGBA"
    # Something should actually be transparent somewhere (the square doesn't
    # fill the whole image), otherwise background removal did nothing.
    alpha = result.getchannel("A")
    assert alpha.getextrema()[0] < 255


def test_remove_background_with_bg_color_flattens_to_solid(sample_image_path: Path):
    data = remove_background(sample_image_path, bg_color=(0, 255, 0))
    result = Image.open(io.BytesIO(data))
    assert result.mode != "RGBA"
    # A corner pixel (outside the foreground square) should be pure green.
    assert result.convert("RGB").getpixel((0, 0)) == (0, 255, 0)


def test_remove_background_bytes_matches_file_based(sample_image_path: Path):
    data_from_path = remove_background(sample_image_path)
    data_from_bytes = remove_background_bytes(sample_image_path.read_bytes())
    assert Image.open(io.BytesIO(data_from_path)).size == Image.open(
        io.BytesIO(data_from_bytes)
    ).size


def test_remove_background_batch(tmp_path: Path, sample_image_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.jpg").write_bytes(sample_image_path.read_bytes())
    (input_dir / "b.jpg").write_bytes(sample_image_path.read_bytes())
    (input_dir / "ignore.txt").write_text("not an image")

    output_dir = tmp_path / "out"
    written = remove_background_batch(input_dir, output_dir)

    assert len(written) == 2
    assert all(p.exists() for p in written)
    assert {p.name for p in written} == {"a.png", "b.png"}


def test_remove_background_batch_missing_dir(tmp_path: Path):
    with pytest.raises(NotADirectoryError):
        remove_background_batch(tmp_path / "nope", tmp_path / "out")
