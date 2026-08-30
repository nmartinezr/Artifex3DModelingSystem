from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import trimesh
from artifex_export import ExportFormat, ExportService


def source_glb(tmp_path: Path) -> Path:
    mesh = trimesh.creation.box(extents=(0.04, 0.03, 0.02))
    path = tmp_path / "source.glb"
    mesh.export(path)
    return path


def test_glb_export_preserves_generated_glb_payload(tmp_path: Path) -> None:
    source = source_glb(tmp_path)
    artifact = ExportService().export_path(source, ExportFormat.GLB)

    assert artifact.media_type == "model/gltf-binary"
    assert artifact.suffix == ".glb"
    assert artifact.content == source.read_bytes()

    output = tmp_path / "roundtrip.glb"
    output.write_bytes(artifact.content)
    loaded = trimesh.load(output, force="mesh")
    assert [round(float(value), 5) for value in loaded.extents] == [0.04, 0.03, 0.02]


def test_stl_export_converts_gltf_meters_to_manufacturing_mm(tmp_path: Path) -> None:
    source = source_glb(tmp_path)
    artifact = ExportService().export_path(source, ExportFormat.STL)

    assert artifact.media_type == "model/stl"
    assert artifact.warning is not None
    output = tmp_path / "roundtrip.stl"
    output.write_bytes(artifact.content)
    loaded = trimesh.load(output, force="mesh")
    assert [round(float(value), 4) for value in loaded.extents] == [40.0, 30.0, 20.0]
    assert len(loaded.faces) == 12


def test_3mf_export_is_standards_package_with_mm_geometry(tmp_path: Path) -> None:
    source = source_glb(tmp_path)
    service = ExportService()
    artifact = service.export_path(source, ExportFormat.THREE_MF)
    repeated = service.export_path(source, ExportFormat.THREE_MF)

    assert artifact.media_type == "model/3mf"
    assert artifact.content == repeated.content

    with ZipFile(io.BytesIO(artifact.content)) as archive:
        assert set(archive.namelist()) == {
            "[Content_Types].xml",
            "_rels/.rels",
            "3D/3dmodel.model",
        }
        root = ET.fromstring(archive.read("3D/3dmodel.model"))

    namespace = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    assert root.attrib["unit"] == "millimeter"
    vertices = root.findall(".//m:vertex", namespace)
    triangles = root.findall(".//m:triangle", namespace)
    assert len(vertices) == 8
    assert len(triangles) == 12

    xs = [float(vertex.attrib["x"]) for vertex in vertices]
    ys = [float(vertex.attrib["y"]) for vertex in vertices]
    zs = [float(vertex.attrib["z"]) for vertex in vertices]
    assert round(max(xs) - min(xs), 4) == 40.0
    assert round(max(ys) - min(ys), 4) == 30.0
    assert round(max(zs) - min(zs), 4) == 20.0
