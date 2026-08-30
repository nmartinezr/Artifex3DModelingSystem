from __future__ import annotations

import sys
from pathlib import Path

import pytest

from artifex_api.image_to_3d import (
    GenerationErrorCode,
    GenerationOptions,
    GenerationRequest,
    ImageAssetRef,
    TrellisProvider,
    TrellisProviderError,
)
from artifex_api.image_to_3d.preprocessing import FileAssetStore


def write_runner(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_trellis_provider_normalizes_assets_and_project_object(tmp_path: Path) -> None:
    store = FileAssetStore(tmp_path / "assets")
    source = store.save(b"image", "image/png", ".png")
    runner = tmp_path / "runner.py"
    write_runner(
        runner,
        """
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--request', required=True)
args = parser.parse_args()
request = json.loads(Path(args.request).read_text(encoding='utf-8'))
out = Path(request['outputDirectory'])
(out / 'model.glb').write_bytes(b'glb-data')
(out / 'albedo.png').write_bytes(b'png-data')
(out / 'result.json').write_text(json.dumps({
    'name': 'Fixture model',
    'conventions': {'unit': 'mm', 'handedness': 'right', 'upAxis': 'Z'},
    'mesh': {
        'path': 'model.glb',
        'mediaType': 'model/gltf-binary',
        'triangleCount': 12,
        'vertexCount': 8,
        'boundsMm': {'min': [-5, -5, 0], 'max': [5, 5, 10]}
    },
    'textures': [{'path': 'albedo.png', 'mediaType': 'image/png'}]
}), encoding='utf-8')
""",
    )

    provider = TrellisProvider(
        store=store,
        command=f"{sys.executable} {runner}",
        model="fixture-model",
        model_version="1",
    )
    result = provider.generate(
        GenerationRequest(
            source_image=ImageAssetRef(source.asset_id, "image/png"),
            options=GenerationOptions(seed=7),
        )
    )

    assert result.mesh_asset.media_type == "model/gltf-binary"
    assert len(result.texture_assets) == 1
    assert result.provenance.provider == "trellis"
    assert result.provenance.model == "fixture-model"
    assert result.project_object is not None
    assert result.project_object["mesh"]["triangleCount"] == 12
    assert result.project_object["mesh"]["bounds"]["max"]["z"] == 10.0
    assert store.resolve(result.mesh_asset.asset_id).read_bytes() == b"glb-data"


def test_trellis_provider_requires_runner_configuration(tmp_path: Path) -> None:
    store = FileAssetStore(tmp_path / "assets")
    source = store.save(b"image", "image/png", ".png")
    provider = TrellisProvider(store=store, command=None)

    with pytest.raises(TrellisProviderError) as exc:
        provider.generate(GenerationRequest(ImageAssetRef(source.asset_id, "image/png")))

    assert exc.value.code == GenerationErrorCode.PROVIDER_UNAVAILABLE


def test_trellis_provider_maps_oom_failure(tmp_path: Path) -> None:
    store = FileAssetStore(tmp_path / "assets")
    source = store.save(b"image", "image/png", ".png")
    runner = tmp_path / "oom.py"
    write_runner(runner, "import sys; print('CUDA out of memory', file=sys.stderr); sys.exit(1)")
    provider = TrellisProvider(store=store, command=f"{sys.executable} {runner}")

    with pytest.raises(TrellisProviderError) as exc:
        provider.generate(GenerationRequest(ImageAssetRef(source.asset_id, "image/png")))

    assert exc.value.code == GenerationErrorCode.RESOURCE_EXHAUSTED


def test_trellis_provider_rejects_non_artifex_conventions(tmp_path: Path) -> None:
    store = FileAssetStore(tmp_path / "assets")
    source = store.save(b"image", "image/png", ".png")
    runner = tmp_path / "bad.py"
    write_runner(
        runner,
        """
import argparse
import json
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('--request', required=True)
args = parser.parse_args()
request = json.loads(Path(args.request).read_text())
out = Path(request['outputDirectory'])
(out / 'model.glb').write_bytes(b'glb')
(out / 'result.json').write_text(json.dumps({
  'conventions': {'unit': 'm', 'handedness': 'right', 'upAxis': 'Y'},
  'mesh': {'path': 'model.glb', 'triangleCount': 1, 'vertexCount': 3,
           'boundsMm': {'min': [0, 0, 0], 'max': [1, 1, 1]}}
}))
""",
    )
    provider = TrellisProvider(store=store, command=f"{sys.executable} {runner}")

    with pytest.raises(TrellisProviderError) as exc:
        provider.generate(GenerationRequest(ImageAssetRef(source.asset_id, "image/png")))

    assert exc.value.code == GenerationErrorCode.INVALID_OUTPUT
