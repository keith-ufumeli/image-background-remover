# bgremover

A simple, always-available background remover: a CLI and a local drag-and-drop web UI,
both built on top of [rembg](https://github.com/danielgatis/rembg) (which does the actual
background-removal work). This project just wraps it in a comfortable interface.

## Install

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -e ".[dev]"
```

This installs the `bgremove` command into your venv's PATH.

**First run downloads a model.** The first time you remove a background, `rembg` downloads
its ONNX model file (~176MB) to `~/.u2net/`. This requires an internet connection once; after
that, it's cached and works offline.

## CLI usage

Remove the background from a single image (writes `photo_nobg.png` next to the original):

```bash
bgremove photo.jpg
```

Choose an output format or a solid background color instead of transparency:

```bash
bgremove photo.jpg --format webp
bgremove photo.jpg --bg-color "#FFFFFF"
bgremove photo.jpg --output result.png
```

Process every image in a folder (writes into `<folder>/output` by default):

```bash
bgremove ./photos --batch
bgremove ./photos --batch --output-dir ./processed --format webp
```

## Web UI

```bash
bgremove serve
```

Then open <http://127.0.0.1:8000> and drag an image in. The server only binds to
`127.0.0.1` — it's a local single-user tool, not exposed on your network.

Use `--port` to change the port: `bgremove serve --port 9000`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests use a synthetic in-memory image fixture (no committed binary test assets) and will
trigger the same first-run model download described above if it hasn't happened yet.

## Project layout

```
src/bgremover/
├── core.py   # background-removal logic (the only module that imports rembg)
├── cli.py    # Typer CLI: single file, --batch folder, `serve`
└── web.py    # FastAPI app + the drag-and-drop page
tests/        # pytest suite for core, CLI, and web layers
```
