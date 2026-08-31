from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import trimesh


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ARTIFEX Stable Fast 3D runner")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument(
        "--sf3d-repo",
        type=Path,
        default=Path(os.getenv("ARTIFEX_SF3D_REPO", "external/stable-fast-3d")),
    )
    parser.add_argument(
        "--python",
        default=os.getenv("ARTIFEX_SF3D_PYTHON", sys.executable),
        help="Python executable from the Stable Fast 3D environment.",
    )
    parser.add_argument(
        "--texture-resolution",
        type=int,
        default=int(os.getenv("ARTIFEX_SF3D_TEXTURE_RESOLUTION", "1024")),
    )
    parser.add_argument(
        "--remesh-option",
        choices=("none", "triangle", "quad"),
        default=os.getenv("ARTIFEX_SF3D_REMESH_OPTION", "none").lower(),
    )
    parser.add_argument(
        "--target-size-mm",
        type=float,
        default=float(os.getenv("ARTIFEX_SF3D_TARGET_SIZE_MM", "100")),
    )
    return parser.parse_args()


def _load_request(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    input_path = Path(str(payload.get("inputPath", ""))).resolve()
    output_dir = Path(str(payload.get("outputDirectory", ""))).resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"ARTIFEX input image not found: {input_path}")
    if not str(payload.get("outputDirectory", "")):
        raise ValueError("ARTIFEX request is missing outputDirectory")
    output_dir.mkdir(parents=True, exist_ok=True)
    payload["_inputPath"] = input_path
    payload["_outputDirectory"] = output_dir
    return payload


def _load_scene(path: Path) -> Any:
    loaded = cast(Any, trimesh.load(path, force="scene"))
    if isinstance(loaded, trimesh.Trimesh):
        scene = trimesh.Scene()
        scene.add_geometry(loaded)
        return scene
    if isinstance(loaded, trimesh.Scene) and loaded.geometry:
        return loaded
    raise ValueError("Stable Fast 3D output contains no mesh geometry")


def _combined_mesh(scene: Any) -> Any:
    geometry = tuple(scene.geometry.values())
    if not geometry:
        raise ValueError("Stable Fast 3D output contains no mesh geometry")
    return cast(Any, trimesh.util.concatenate(geometry))


def _normalize_scene(scene: Any, target_size_mm: float) -> None:
    if target_size_mm <= 0:
        return
    bounds = scene.bounds
    extents = bounds[1] - bounds[0]
    largest_extent = float(max(extents))
    if largest_extent <= 0:
        raise ValueError("Stable Fast 3D output has invalid dimensions")
    # GLB convention is meters; ARTIFEX manufacturing dimensions are millimeters.
    scale = (target_size_mm / 1000.0) / largest_extent
    scene.apply_transform(trimesh.transformations.scale_matrix(scale))


def main() -> int:
    args = _parse_args()
    request = _load_request(args.request)
    input_path: Path = request["_inputPath"]
    output_dir: Path = request["_outputDirectory"]

    sf3d_repo = args.sf3d_repo.resolve()
    run_script = sf3d_repo / "run.py"
    if not run_script.is_file():
        raise FileNotFoundError(
            "Stable Fast 3D is not installed. Clone Stability-AI/stable-fast-3d and set "
            "ARTIFEX_SF3D_REPO to that repository directory."
        )

    engine_output = output_dir / "engine"
    engine_output.mkdir(parents=True, exist_ok=True)
    command = [
        args.python,
        str(run_script),
        str(input_path),
        "--output-dir",
        str(engine_output),
        "--texture-resolution",
        str(args.texture_resolution),
        "--remesh_option",
        args.remesh_option,
    ]
    completed = subprocess.run(
        command,
        cwd=sf3d_repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "Stable Fast 3D failed"
        raise RuntimeError(message)

    glb_files = sorted(engine_output.rglob("*.glb"))
    if not glb_files:
        raise FileNotFoundError("Stable Fast 3D completed but produced no GLB output")

    scene = _load_scene(glb_files[0])
    _normalize_scene(scene, args.target_size_mm)
    mesh = _combined_mesh(scene)
    normalized_path = output_dir / "model.glb"
    normalized_path.write_bytes(scene.export(file_type="glb"))

    bounds_m = scene.bounds
    result = {
        "name": "Stable Fast 3D model",
        "conventions": {"unit": "mm", "handedness": "right", "upAxis": "Z"},
        "mesh": {
            "path": normalized_path.name,
            "mediaType": "model/gltf-binary",
            "triangleCount": int(len(mesh.faces)),
            "vertexCount": int(len(mesh.vertices)),
            "boundsMm": {
                "min": [float(value) * 1000.0 for value in bounds_m[0]],
                "max": [float(value) * 1000.0 for value in bounds_m[1]],
            },
        },
        "textures": [],
        "runner": {
            "provider": "stable-fast-3d",
            "model": str(request.get("model") or "stabilityai/stable-fast-3d"),
            "textureResolution": args.texture_resolution,
            "remeshOption": args.remesh_option,
            "targetSizeMm": args.target_size_mm,
        },
    }
    (output_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
