"""Typer CLI: process a single image, batch-process a folder, or serve the web UI.

This is deliberately a single Typer command (not a Group with subcommands): mixing a
group-level positional argument with a registered subcommand makes Click misparse any
option that appears after the positional value (it tries to treat the option as a
subcommand name). `serve` is instead handled as a special value of the `path` argument,
which keeps this a single Click Command and preserves normal any-order option parsing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from bgremover.core import (
    UnsupportedFormatError,
    parse_hex_color,
    remove_background,
    remove_background_batch,
)

app = typer.Typer(help="Remove backgrounds from images.")


def _parse_bg_color_option(value: Optional[str]) -> Optional[tuple[int, int, int]]:
    if value is None:
        return None
    try:
        return parse_hex_color(value)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command()
def main(
    path: Path = typer.Argument(
        ..., help="Image file, a folder when --batch is set, or 'serve' to launch the web UI"
    ),
    batch: bool = typer.Option(False, "--batch", help="Treat PATH as a folder of images"),
    output_format: str = typer.Option(
        "png", "--format", help="Output format: png or webp"
    ),
    bg_color: Optional[str] = typer.Option(
        None, "--bg-color", help="Hex color e.g. #FFFFFF; default is transparent"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", help="Output file path (single-image mode)"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", help="Output folder (batch mode, default: <PATH>/output)"
    ),
    port: int = typer.Option(8000, "--port", help="Port to serve on (with 'serve')"),
) -> None:
    if str(path) == "serve":
        import uvicorn

        uvicorn.run("bgremover.web:app", host="127.0.0.1", port=port)
        return

    if output_format not in ("png", "webp"):
        typer.echo(f"Error: --format must be 'png' or 'webp', got {output_format!r}", err=True)
        raise typer.Exit(code=1)

    color = _parse_bg_color_option(bg_color)

    try:
        if batch:
            resolved_output_dir = output_dir or (path / "output")
            written = remove_background_batch(path, resolved_output_dir, output_format, color)
            for out_path in written:
                typer.echo(f"Wrote {out_path}")
            typer.echo(f"Processed {len(written)} image(s) into {resolved_output_dir}")
        else:
            data = remove_background(path, output_format, color)
            resolved_output = output or path.with_name(f"{path.stem}_nobg.{output_format}")
            resolved_output.write_bytes(data)
            typer.echo(f"Wrote {resolved_output}")
    except (FileNotFoundError, NotADirectoryError, UnsupportedFormatError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
