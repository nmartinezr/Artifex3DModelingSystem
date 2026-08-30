from __future__ import annotations

import io
from zipfile import ZipFile

from fastapi.testclient import TestClient
from PIL import Image

from artifex_api.main import app


def _png_bytes() -> bytes:
    image = Image.new("RGB", (64, 64), "white")
    for x in range(16, 48):
        for y in range(16, 48):
            image.putpixel((x, y), (32, 96, 160))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_image_to_3d_fixture_generation_validation_and_exports() -> None:
    client = TestClient(app)
    generation = client.post(
        "/v1/image-to-3d/generate?provider=fixture",
        files={"file": ("fixture.png", _png_bytes(), "image/png")},
    )

    assert generation.status_code == 200
    payload = generation.json()
    assert payload["correlation_id"].startswith("gen_")
    assert payload["provider"] == "fixture"
    assert payload["analysis"]["exportBlocked"] is False
    assert payload["analysis"]["metrics"]["triangleCount"] == 12
    assert payload["analysis"]["metrics"]["componentCount"] == 1
    assert payload["analysis"]["metrics"]["watertight"] is True
    mesh_asset_id = payload["mesh_asset_id"]

    for export_format, media_type in (
        ("glb", "model/gltf-binary"),
        ("stl", "model/stl"),
        ("3mf", "model/3mf"),
    ):
        response = client.post(f"/v1/exports/{mesh_asset_id}?format={export_format}")
        assert response.status_code == 200
        exported = response.json()
        assert exported["format"] == export_format
        assert exported["media_type"] == media_type
        asset = client.get(f"/v1/assets/{exported['export_asset_id']}")
        assert asset.status_code == 200
        assert len(asset.content) > 0
        if export_format == "3mf":
            with ZipFile(io.BytesIO(asset.content)) as archive:
                assert "3D/3dmodel.model" in archive.namelist()
