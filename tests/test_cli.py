from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from bgremover.cli import app

runner = CliRunner()


def test_cli_missing_file_exits_nonzero(tmp_path: Path):
    result = runner.invoke(app, [str(tmp_path / "missing.jpg")])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_cli_processes_single_file(sample_image_path: Path):
    result = runner.invoke(app, [str(sample_image_path)])
    assert result.exit_code == 0
    expected_output = sample_image_path.with_name(
        f"{sample_image_path.stem}_nobg.png"
    )
    assert expected_output.exists()


def test_cli_batch_processes_folder(tmp_path: Path, sample_image_path: Path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.jpg").write_bytes(sample_image_path.read_bytes())

    result = runner.invoke(app, [str(input_dir), "--batch"])
    assert result.exit_code == 0
    assert (input_dir / "output" / "a.png").exists()


def test_cli_rejects_bad_bg_color(sample_image_path: Path):
    result = runner.invoke(app, [str(sample_image_path), "--bg-color", "nothex"])
    assert result.exit_code != 0
