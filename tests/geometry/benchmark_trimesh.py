from __future__ import annotations

import json
import time
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "geometry"


def analyze(path: Path) -> dict:
    started = time.perf_counter()
    loaded = trimesh.load(path, force="scene")
    if isinstance(loaded, trimesh.Scene):
        meshes = tuple(loaded.geometry.values())
    else:
        meshes = (loaded,)

    if not meshes:
        raise RuntimeError(f"No meshes loaded from {path}")

    merged = trimesh.util.concatenate(meshes)
    components = merged.split(only_watertight=False)
    elapsed_ms = (time.perf_counter() - started) * 1000

    extents = [float(value) for value in merged.extents]
    volume = float(merged.volume) if merged.is_volume else None
    return {
        "path": str(path),
        "durationMs": round(elapsed_ms, 3),
        "vertices": len(merged.vertices),
        "triangles": len(merged.faces),
        "componentCount": len(components),
        "watertight": bool(merged.is_watertight),
        "isVolume": bool(merged.is_volume),
        "volumeMm3": volume,
        "boundsMm": extents,
    }


def main() -> None:
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    output = [analyze(FIXTURES / fixture["path"]) for fixture in manifest["fixtures"]]
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
