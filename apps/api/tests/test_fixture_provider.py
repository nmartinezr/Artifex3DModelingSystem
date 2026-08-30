from __future__ import annotations

import struct
from pathlib import Path

from artifex_api.image_to_3d.contracts import GenerationRequest, ImageAssetRef
from artifex_api.image_to_3d.fixture_provider import FixtureImageTo3DProvider
from artifex_api.image_to_3d.preprocessing import FileAssetStore


def test_fixture_provider_persists_valid_glb_and_project_object(tmp_path: Path) -> None:
    store = FileAssetStore(tmp_path / "assets")
    provider = FixtureImageTo3DProvider(store=store)

    result = provider.generate(
        GenerationRequest(source_image=ImageAssetRef("asset_source", "image/png"))
    )

    path = store.resolve(result.mesh_asset.asset_id)
    content = path.read_bytes()
    magic, version, declared_length = struct.unpack("<4sII", content[:12])

    assert magic == b"glTF"
    assert version == 2
    assert declared_length == len(content)
    assert result.provenance.provider == "fixture"
    assert result.project_object is not None
    assert result.project_object["mesh"]["triangleCount"] == 12
    assert result.project_object["mesh"]["vertexCount"] == 24
