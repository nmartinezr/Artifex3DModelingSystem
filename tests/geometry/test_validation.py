from __future__ import annotations

from pathlib import Path

import pytest
import trimesh
from artifex_geometry import TrimeshMeshValidator


def test_valid_glb_box_reports_manufacturing_metrics_in_mm(tmp_path: Path) -> None:
    mesh = trimesh.creation.box(extents=(0.04, 0.03, 0.02))
    path = tmp_path / "box.glb"
    mesh.export(path)

    report = TrimeshMeshValidator().validate_path(path)

    assert report.valid_mesh is True
    assert report.export_blocked is False
    assert report.triangle_count == 12
    assert report.vertex_count == 8
    assert report.component_count == 1
    assert report.watertight is True
    assert report.manifold is True
    assert report.boundary_edge_count == 0
    assert report.volume_mm3 is not None
    assert report.volume_mm3 == pytest.approx(24000.0, abs=0.01)
    assert report.dimensions_mm is not None
    assert report.dimensions_mm == pytest.approx([40.0, 30.0, 20.0], abs=0.001)


def test_open_mesh_reports_boundaries_without_mutating_source(tmp_path: Path) -> None:
    mesh = trimesh.Trimesh(
        vertices=[[0, 0, 0], [10, 0, 0], [0, 10, 0], [0, 0, 10]],
        faces=[[0, 1, 2], [0, 3, 1], [0, 2, 3]],
        process=False,
    )
    original_vertices = mesh.vertices.copy()
    path = tmp_path / "open.stl"
    mesh.export(path)

    report = TrimeshMeshValidator().validate_path(path)

    assert report.watertight is False
    assert report.boundary_edge_count == 3
    assert any(finding.code == "MESH_OPEN_BOUNDARIES" for finding in report.findings)
    assert (mesh.vertices == original_vertices).all()


def test_invalid_file_blocks_export(tmp_path: Path) -> None:
    path = tmp_path / "invalid.glb"
    path.write_bytes(b"not-a-model")

    report = TrimeshMeshValidator().validate_path(path)

    assert report.valid_mesh is False
    assert report.export_blocked is True
    assert report.findings[0].code == "MESH_LOAD_FAILED"
