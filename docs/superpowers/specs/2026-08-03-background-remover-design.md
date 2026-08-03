# Background Remover — Design

**Date:** 2026-08-03
**Status:** Approved

## Purpose

A simple, always-available tool for removing image backgrounds, built for personal use by a
frontend developer. Replaces ad-hoc use of `pip install rembg` (the user's earlier reference
to "remb" was this package) with a proper, reusable, installable project: one core library,
exposed through both a CLI and a local web UI.

## Background

- Working directory started empty (blank `main.py`, no commits).
- `rembg` (v2.0.77) is already installed locally and is a mature, actively maintained
  background-removal library (ONNX/U²-Net based, CPU-friendly, no GPU required). The design
  wraps `rembg` rather than reimplementing background removal — the value being added here is
  clean packaging and a comfortable interface, not a new ML model.

## Goals

- One installable Python package providing a single CLI entry point: `bgremove`.
- Support both a single-image workflow and folder/batch processing.
- Support both a CLI and a local web UI (drag-and-drop), sharing one core implementation.
- Configurable output: transparent PNG (default), WEBP, or flattened onto a solid background
  color.
- No system-level integration (no context-menu install, no auto-start service) — this is a
  tool the user runs on demand from a terminal or by starting the local web server.

## Non-goals

- No reimplementation of the background-removal model itself (delegated entirely to `rembg`).
- No authentication, multi-user support, job queues, or persistence in the web UI — it is a
  local, single-user tool bound to `127.0.0.1`.
- No GPU-specific optimization.
- No OS-level shell integration (e.g. Explorer context menu) in this iteration.

## Architecture

Single Python package, `bgremover`, installed via `pyproject.toml` with one console-script
entry point (`bgremove`). Project layout:

```
image-background-remover/
├── pyproject.toml
├── README.md
├── src/
│   └── bgremover/
│       ├── __init__.py
│       ├── core.py         # remove_background(), remove_background_batch()
│       ├── cli.py          # Typer app: single file, batch, `serve`
│       └── web.py          # FastAPI app + one static HTML page (drag-and-drop)
└── tests/
    ├── test_core.py
    ├── test_cli.py
    ├── test_web.py
    └── fixtures/
        └── sample.jpg
```

`core.py` is the only module that imports `rembg`. `cli.py` and `web.py` are thin wrappers
that call into `core` and handle their own I/O (filesystem vs HTTP upload) — neither touches
image processing directly. This keeps each layer independently testable and swappable.

### Core module (`core.py`)

```python
def remove_background(
    input_path: Path,
    output_format: Literal["png", "webp"] = "png",
    bg_color: tuple[int, int, int] | None = None,  # None = transparent
) -> bytes: ...

def remove_background_batch(
    input_dir: Path,
    output_dir: Path,
    output_format: str = "png",
    bg_color: tuple[int, int, int] | None = None,
) -> list[Path]: ...
```

- Wraps `rembg.remove()`. Batch mode creates a single `rembg` session and reuses it across all
  files (model loading is the expensive part — must not reload per image).
- When `bg_color` is provided, the transparent result is composited onto a solid color using
  Pillow before encoding; otherwise the alpha channel is preserved as-is.
- Raises explicit exceptions (`UnsupportedFormatError`, `FileNotFoundError`) rather than
  failing silently. Both CLI and web layers catch these and surface a friendly
  message/appropriate HTTP status.

### CLI (`cli.py`, built with Typer)

```
bgremove IMAGE_PATH [--format png|webp] [--bg-color "#RRGGBB"] [--output PATH]
bgremove FOLDER_PATH --batch [--format ...] [--bg-color ...] [--output-dir PATH]
bgremove serve [--port 8000]
```

- Single-file processing is the default mode.
- Passing a directory requires the explicit `--batch` flag (no silent whole-folder walks).
- Batch runs show progress via `tqdm` (already a transitive dependency of `rembg`).
- `bgremove serve` launches the web UI (see below) via `uvicorn`.

### Web UI (`web.py`, FastAPI)

- Single page: drag-and-drop or click-to-browse an image, plus controls for output format and
  optional background color.
- One endpoint, `POST /remove`, returns the processed image for preview and download.
- No auth, no persistence, no job queue — single-user, synchronous request/response.
- `bgremove serve` binds `uvicorn` to `127.0.0.1` only; never exposed on the network.

## Error handling

- Core raises typed exceptions for bad input (missing file, unsupported extension).
- CLI: caught and reported as a clear stderr message with non-zero exit code.
- Web: caught and reported as a 4xx JSON response with a human-readable `detail` message.

## Testing

- `test_core.py`: unit tests against a small fixture image — assert transparent output has an
  alpha channel, bg-color output has the expected solid color, and bad inputs raise the
  correct exceptions.
- `test_cli.py`: Typer `CliRunner` smoke tests — invalid path exits non-zero, valid path
  produces an output file.
- `test_web.py`: FastAPI `TestClient` test hitting `POST /remove` with a sample upload.
- No tests assert on the visual/quality output of the background-removal model itself — that
  correctness is `rembg`'s responsibility, not this project's.

## Packaging & distribution

- `pyproject.toml` with a `[project.scripts]` entry: `bgremove = "bgremover.cli:app"`.
- Install locally with `pip install -e .` (editable install) so `bgremove` is available as a
  command from anywhere the venv is active.
- Dependencies: `rembg`, `typer`, `fastapi`, `uvicorn`, `pillow`, `python-multipart` (for
  FastAPI file uploads), plus `pytest`/`httpx` for tests.
- README covers: prerequisites, install steps (venv + `pip install -e .`), CLI usage examples,
  how to start the web UI, and troubleshooting notes for first-run model download (rembg
  downloads its ONNX model file on first use).

## Open questions / decisions deferred

None outstanding — all clarified during brainstorming. Future iterations (not in scope now)
could add: OS-level context-menu integration, a packaged standalone `.exe`, or a persistent
background service.
