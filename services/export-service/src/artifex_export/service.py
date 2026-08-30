from __future__ import annotations

import io
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, cast
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import trimesh  # type: ignore[import-untyped]


class ExportFormat(str, Enum):
    GLB = "glb"
    STL = "stl"
    THREE_MF = "3mf"


class ExportError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ExportArtifact:
    content: bytes
    media_type: str
    suffix: str
    warning: str | None = None


class ExportService:
    """Provider-neutral manufacturing export service for ARTIFEX mesh assets."""

    def export_path(self, source: Path, export_format: ExportFormat) -> ExportArtifact:
        if not source.is_file():
            raise ExportError("EXPORT_SOURCE_NOT_FOUND", "Source mesh asset was not found")

        if export_format is ExportFormat.GLB and source.suffix.lower() == ".glb":
            return ExportArtifact(source.read_bytes(), "model/gltf-binary", ".glb")

        mesh = self._load_mesh_in_mm(source)
        if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            raise ExportError("EXPORT_INVALID_MESH", "Source mesh contains no triangles")

        try:
            if export_format is ExportFormat.GLB:
                glb_mesh = mesh.copy()
                glb_mesh.apply_scale(0.001)
                content = cast(bytes, glb_mesh.export(file_type="glb"))  # type: ignore[no-untyped-call]
                return ExportArtifact(content, "model/gltf-binary", ".glb")

            if export_format is ExportFormat.STL:
                content = cast(bytes, mesh.export(file_type="stl"))  # type: ignore[no-untyped-call]
                return ExportArtifact(
                    content,
                    "model/stl",
                    ".stl",
                    "STL stores geometry only; colors, materials and textures are not preserved.",
                )

            if export_format is ExportFormat.THREE_MF:
                return ExportArtifact(
                    self._export_3mf(mesh),
                    "model/3mf",
                    ".3mf",
                )
        except ExportError:
            raise
        except Exception as exc:
            raise ExportError(
                "EXPORT_GEOMETRY_FAILED",
                f"Failed to export mesh as {export_format.value}",
            ) from exc

        raise ExportError("EXPORT_FORMAT_UNSUPPORTED", f"Unsupported export: {export_format.value}")

    def _load_mesh_in_mm(self, source: Path) -> Any:
        try:
            loaded = cast(Any, trimesh.load(source, force="scene"))  # type: ignore[no-untyped-call]
            if isinstance(loaded, trimesh.Scene):
                meshes = tuple(loaded.geometry.values())
                if not meshes:
                    raise ExportError("EXPORT_INVALID_MESH", "Source contains no mesh geometry")
                mesh = cast(Any, trimesh.util.concatenate(meshes))  # type: ignore[no-untyped-call]
            else:
                mesh = loaded
        except ExportError:
            raise
        except Exception as exc:
            raise ExportError("EXPORT_SOURCE_INVALID", "Source mesh could not be decoded") from exc

        if source.suffix.lower() in {".glb", ".gltf"}:
            mesh = mesh.copy()
            mesh.apply_scale(1000.0)
        return mesh

    def _export_3mf(self, mesh: Any) -> bytes:
        vertices = [[float(component) for component in vertex] for vertex in mesh.vertices]
        faces = [[int(index) for index in face] for face in mesh.faces]
        model_xml = self._model_xml(vertices, faces).encode("utf-8")

        content_types = b"""<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>"""
        relationships = b"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""

        output = io.BytesIO()
        with ZipFile(output, mode="w", compression=ZIP_DEFLATED) as archive:
            self._write_zip_entry(archive, "[Content_Types].xml", content_types)
            self._write_zip_entry(archive, "_rels/.rels", relationships)
            self._write_zip_entry(archive, "3D/3dmodel.model", model_xml)
        return output.getvalue()

    @staticmethod
    def _write_zip_entry(archive: ZipFile, name: str, content: bytes) -> None:
        info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, content)

    @staticmethod
    def _model_xml(vertices: list[list[float]], faces: list[list[int]]) -> str:
        vertex_xml = "".join(
            f'<vertex x="{x:.9g}" y="{y:.9g}" z="{z:.9g}"/>' for x, y, z in vertices
        )
        triangle_xml = "".join(
            f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<model unit="millimeter" xml:lang="en-US" '
            'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
            '<metadata name="Application">ARTIFEX</metadata>'
            '<resources><object id="1" type="model"><mesh>'
            f'<vertices>{vertex_xml}</vertices>'
            f'<triangles>{triangle_xml}</triangles>'
            '</mesh></object></resources>'
            '<build><item objectid="1"/></build>'
            '</model>'
        )
