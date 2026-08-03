from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from bgremover.web import app

client = TestClient(app)


def test_index_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_remove_endpoint_returns_png(sample_image_path: Path):
    with sample_image_path.open("rb") as f:
        response = client.post(
            "/remove",
            files={"file": ("sample.jpg", f, "image/jpeg")},
            data={"format": "png"},
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_remove_endpoint_rejects_bad_format(sample_image_path: Path):
    with sample_image_path.open("rb") as f:
        response = client.post(
            "/remove",
            files={"file": ("sample.jpg", f, "image/jpeg")},
            data={"format": "tiff"},
        )
    assert response.status_code == 400


def test_remove_endpoint_rejects_non_image():
    response = client.post(
        "/remove",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
        data={"format": "png"},
    )
    assert response.status_code == 400
