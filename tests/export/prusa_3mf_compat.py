from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import trimesh

from artifex_export import ExportFormat, ExportService


def main() -> None:
    work = Path(".artifex-compat")
    work.mkdir(exist_ok=True)

    source = work / "source.glb"
    trimesh.creation.box(extents=(0.04, 0.03, 0.02)).export(source)
    artifact = ExportService().export_path(source, ExportFormat.THREE_MF)
    generated_3mf = work / "artifex.3mf"
    generated_3mf.write_bytes(artifact.content)

    output_stl = work / "prusa-reloaded.stl"
    command = [
        "xvfb-run",
        "-a",
        "prusa-slicer",
        "--export-stl",
        "--output",
        str(output_stl),
        str(generated_3mf),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    if not output_stl.is_file():
        raise RuntimeError("PrusaSlicer did not produce an STL from the ARTIFEX 3MF")

    reloaded = trimesh.load(output_stl, force="mesh")
    expected = [40.0, 30.0, 20.0]
    actual = [float(value) for value in reloaded.extents]
    if any(abs(left - right) > 0.01 for left, right in zip(actual, expected, strict=True)):
        raise AssertionError(f"PrusaSlicer round-trip changed dimensions: {actual} != {expected}")
    if len(reloaded.faces) != 12:
        raise AssertionError(f"Unexpected triangle count after PrusaSlicer reload: {len(reloaded.faces)}")

    print(f"PrusaSlicer accepted ARTIFEX 3MF; dimensions={actual}, triangles={len(reloaded.faces)}")


if __name__ == "__main__":
    main()
