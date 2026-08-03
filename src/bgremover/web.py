"""Local single-user web UI: drag-and-drop an image, get the background removed."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response

from bgremover.core import parse_hex_color, remove_background_bytes

app = FastAPI(title="Background Remover")

_INDEX_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Background Remover</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 3rem auto; }
  #drop { border: 2px dashed #888; border-radius: 8px; padding: 3rem; text-align: center; color: #555; }
  #drop.dragover { background: #eef; border-color: #33f; }
  #controls { margin: 1rem 0; display: flex; gap: 1rem; align-items: center; }
  #preview { max-width: 100%; margin-top: 1rem; }
  #status { color: #a00; }
</style>
</head>
<body>
<h1>Background Remover</h1>
<div id="drop">Drag an image here, or click to choose a file</div>
<input id="file-input" type="file" accept="image/*" style="display:none">
<div id="controls">
  <label>Format:
    <select id="format"><option value="png">PNG</option><option value="webp">WEBP</option></select>
  </label>
  <label>Background:
    <input id="bg-color" type="color" value="#ffffff">
    <input id="use-bg" type="checkbox"> use solid color (unchecked = transparent)
  </label>
</div>
<p id="status"></p>
<img id="preview" style="display:none">
<a id="download" style="display:none" download="result.png">Download result</a>

<script>
const drop = document.getElementById('drop');
const fileInput = document.getElementById('file-input');
const status = document.getElementById('status');
const preview = document.getElementById('preview');
const download = document.getElementById('download');

drop.addEventListener('click', () => fileInput.click());
drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('dragover'); });
drop.addEventListener('dragleave', () => drop.classList.remove('dragover'));
drop.addEventListener('drop', (e) => {
  e.preventDefault();
  drop.classList.remove('dragover');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

async function handleFile(file) {
  status.textContent = 'Processing...';
  preview.style.display = 'none';
  download.style.display = 'none';

  const format = document.getElementById('format').value;
  const useBg = document.getElementById('use-bg').checked;
  const bgColor = document.getElementById('bg-color').value;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('format', format);
  if (useBg) formData.append('bg_color', bgColor);

  try {
    const resp = await fetch('/remove', { method: 'POST', body: formData });
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({detail: resp.statusText}));
      throw new Error(detail.detail || resp.statusText);
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    preview.src = url;
    preview.style.display = 'block';
    download.href = url;
    download.download = `result.${format}`;
    download.style.display = 'inline';
    download.textContent = 'Download result';
    status.textContent = '';
  } catch (err) {
    status.textContent = 'Error: ' + err.message;
  }
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML


@app.post("/remove")
async def remove_endpoint(
    file: UploadFile = File(...),
    format: str = Form("png"),
    bg_color: Optional[str] = Form(None),
) -> Response:
    if format not in ("png", "webp"):
        raise HTTPException(status_code=400, detail="format must be 'png' or 'webp'")

    color = None
    if bg_color:
        try:
            color = parse_hex_color(bg_color)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    data = await file.read()
    try:
        result = remove_background_bytes(data, format, color)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not process image: {exc}") from exc

    media_type = "image/png" if format == "png" else "image/webp"
    return Response(content=result, media_type=media_type)
