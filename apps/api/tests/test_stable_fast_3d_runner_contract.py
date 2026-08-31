from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = REPO_ROOT / "tools" / "image_to_3d" / "stable_fast_3d_runner.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("artifex_sf3d_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fake_sf3d(repo: Path) -> None:
    repo.mkdir(parents=True)
    (repo / "run.py").write_text(
        """
import argparse
from pathlib import Path
import trimesh

parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('--output-dir', required=True)
parser.add_argument('--texture-resolution')
parser.add_argument('--remesh_option')
args = parser.parse_args()
out = Path(args.output_dir)
out.mkdir(parents=True, exist_ok=True)
mesh = trimesh.creation.box(extents=(1.0, 0.5, 0.25))
mesh.export(out / 'fake.glb')
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_runner_normalizes_real_engine_output_to_artifex_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _load_runner()
    sf3d_repo = tmp_path / "stable-fast-3d"
    _write_fake_sf3d(sf3d_repo)
    input_path = tmp_path / "source.png"
    input_path.write_bytes(b"fake-image")
    output_dir = tmp_path / "output"
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "inputPath": str(input_path),
                "outputDirectory": str(output_dir),
                "model": "stabilityai/stable-fast-3d",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RUNNER_PATH),
            "--request",
            str(request_path),
            "--sf3d-repo",
            str(sf3d_repo),
            "--target-size-mm",
            "100",
        ],
    )

    assert runner.main() == 0
    assert (output_dir / "model.glb").is_file()
    manifest = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
    assert manifest["mesh"]["mediaType"] == "model/gltf-binary"
    assert manifest["mesh"]["triangleCount"] > 0
    assert manifest["mesh"]["vertexCount"] > 0
    assert manifest["runner"]["provider"] == "stable-fast-3d"
    assert manifest["runner"]["targetSizeMm"] == 100.0
    dimensions = [
        manifest["mesh"]["boundsMm"]["max"][index]
        - manifest["mesh"]["boundsMm"]["min"][index]
        for index in range(3)
    ]
    assert max(dimensions) == pytest.approx(100.0)


def test_runner_reports_missing_sf3d_installation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _load_runner()
    input_path = tmp_path / "source.png"
    input_path.write_bytes(b"fake-image")
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {"inputPath": str(input_path), "outputDirectory": str(tmp_path / "output")}
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RUNNER_PATH),
            "--request",
            str(request_path),
            "--sf3d-repo",
            str(tmp_path / "missing"),
        ],
    )

    with pytest.raises(FileNotFoundError, match="ARTIFEX_SF3D_REPO"):
        runner.main()
