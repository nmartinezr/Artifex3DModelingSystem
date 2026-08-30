from __future__ import annotations

import json
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "geometry"


def load_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="scene")
    meshes = tuple(loaded.geometry.values()) if isinstance(loaded, trimesh.Scene) else (loaded,)
    assert meshes
    return trimesh.util.concatenate(meshes)


def test_geometry_fixtures_match_manifest() -> None:
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))

    for fixture in manifest["fixtures"]:
        mesh = load_mesh(FIXTURES / fixture["path"])
        expected = fixture["expected"]

        if "watertight" in expected:
            assert mesh.is_watertight is expected["watertight"], fixture["id"]

        components = mesh.split(only_watertight=False)
        assert len(components) == expected["componentCount"], fixture["id"]

        if "boundsMm" in expected:
            assert [round(float(value), 5) for value in mesh.extents] == expected["boundsMm"]

        if "volumeMm3" in expected:
            assert round(float(mesh.volume), 5) == expected["volumeMm3"]
