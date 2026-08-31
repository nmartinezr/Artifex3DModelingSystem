from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any, cast

import trimesh


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Adapt a CLI Image-to-3D engine to the ARTIFEX runner manifest contract."
    )
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument(
        "--engine-command",
        required=True,
        help=(
            "Command template. Supported placeholders: {input}, {engine_output}, {model}, "
            "{seed}, {quality}."
        ),
    )
    parser.add_argument(
        "--mesh-glob",
        default="**/*.glb",
        help="Glob used inside the engine output directory to locate the generated GLB.",
    )
    parser.add_argument(
        "--target-size-mm",
        default=100.0,
        type=float,
        help="Normalize the largest model dimension to this size in millimeters; <= 0 disables scaling.",
    )
    return parser.parse_args()


def _load_scene(path: Path) -> Any:
    loaded = cast(Any, trimesh.load(path, force="scene"))
    if isinstance(loaded, trimesh.Scene):
        if not loaded.geometry:
            raise ValueError("Generated GLB contains no mesh geometry")
        return loaded
    if isinstance(loaded, trimesh.Trimesh):
        scene = trimesh.Scene()
        scene.add_geometry(loaded)
        return scene
    raise ValueError("Generated asset is not a mesh")


def _combined_mesh(scene: Any) -> Any:
    geometries = tuple(scene.geometry.values())
    if not geometries:
        raise ValueError("Generated GLB contains no mesh geometry")
    return cast(Any, trimesh.util.concatenate(geometries))


def _normalize_scene(scene: Any, target_size_mm: float) -> None:
    if target_size_mm <= 0:
        return
    mesh = _combined_mesh(scene)
    largest_extent = float(max(mesh.extents))
    if largest_extent <= 0:
        raise ValueError("Generated mesh has invalid dimensions")
    target_extent_m = target_size_mm / 1000.0
    scale = target_extent_m / largest_extent
    scene.apply_transform(trimesh.transformations.scale_matrix(scale))


def main() -> int:
    args = _parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    input_path = Path(request["inputPath"]).resolve()
    output_dir = Path(request["outputDirectory"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    engine_output = output_dir / "engine"
    engine_output.mkdir(parents=True, exist_ok=True)

    values = {
        "input": str(input_path),
        "engine_output": str(engine_output),
        "model": str(request.get("model") or ""),
        "seed": str(request.get("seed") if request.get("seed") is not None else 0),
        "quality": str(request.get("quality") or "balanced"),
    }
    command_text = args.engine_command.format(**values)
    completed = subprocess.run(
        shlex.split(command_text),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        if completed.stderr:
            print(completed.stderr, end="")
        return completed.returncode

    matches = sorted(engine_output.glob(args.mesh_glob))
    if not matches:
        raise FileNotFoundError(
            f"Engine completed successfully but no GLB matched {args.mesh_glob!r} in {engine_output}"
        )

    scene = _load_scene(matches[0])
    _normalize_scene(scene, args.target_size_mm)
    mesh = _combined_mesh(scene)
    normalized_path = output_dir / "model.glb"
    normalized_path.write_bytes(scene.export(file_type="glb"))

    bounds_m = mesh.bounds
    bounds_mm = {
        "min": [float(value) * 1000.0 for value in bounds_m[0]],
        "max": [float(value) * 1000.0 for value in bounds_m[1]],
    }
    result = {
        "name": "Generated model",
        "conventions": {"unit": "mm", "handedness": "right", "upAxis": "Z"},
        "mesh": {
            "path": normalized_path.name,
            "mediaType": "model/gltf-binary",
            "triangleCount": int(len(mesh.faces)),
            "vertexCount": int(len(mesh.vertices)),
            "boundsMm": bounds_mm,
        },
        "textures": [],
        "runner": {
            "engineCommand": shlex.split(args.engine_command)[0],
            "targetSizeMm": args.target_size_mm,
        },
    }
    (output_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
