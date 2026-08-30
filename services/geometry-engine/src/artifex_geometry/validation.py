from __future__ import annotations

import math
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import trimesh  # type: ignore[import-untyped]


@dataclass(frozen=True)
class MeshFinding:
    code: str
    severity: str
    message: str
    details: dict[str, Any]


@dataclass(frozen=True)
class MeshValidationReport:
    valid_mesh: bool
    export_blocked: bool
    vertex_count: int
    triangle_count: int
    component_count: int
    bounds_mm: dict[str, list[float]] | None
    dimensions_mm: list[float] | None
    watertight: bool | None
    manifold: bool | None
    boundary_edge_count: int | None
    non_manifold_edge_count: int | None
    degenerate_face_count: int | None
    winding_consistent: bool | None
    volume_mm3: float | None
    duration_ms: float
    findings: tuple[MeshFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TrimeshMeshValidator:
    """Read-only M1 mesh quality gate. It never mutates or repairs the source mesh."""

    def validate_path(self, path: Path) -> MeshValidationReport:
        started = time.perf_counter()
        findings: list[MeshFinding] = []
        try:
            loaded = cast(Any, trimesh.load(path, force="scene"))  # type: ignore[no-untyped-call]
            if isinstance(loaded, trimesh.Scene):
                meshes = tuple(loaded.geometry.values())
                if not meshes:
                    return self._invalid(started, "MESH_EMPTY", "The model contains no mesh geometry.")
                mesh = cast(Any, trimesh.util.concatenate(meshes))  # type: ignore[no-untyped-call]
            else:
                mesh = loaded
        except Exception as exc:
            return self._invalid(
                started,
                "MESH_LOAD_FAILED",
                "The generated model could not be decoded as mesh geometry.",
                {"errorType": type(exc).__name__},
            )

        vertex_count = int(len(mesh.vertices))
        triangle_count = int(len(mesh.faces))
        if vertex_count == 0 or triangle_count == 0:
            return self._invalid(started, "MESH_EMPTY", "The model contains no printable triangles.")

        length_factor = self._length_factor_to_mm(path)
        bounds_raw = [
            [float(value) * length_factor for value in row]
            for row in mesh.bounds
        ]
        dimensions = [float(value) * length_factor for value in mesh.extents]
        finite_geometry = all(math.isfinite(value) for row in bounds_raw for value in row)
        finite_geometry = finite_geometry and all(math.isfinite(value) for value in dimensions)
        if not finite_geometry:
            findings.append(
                MeshFinding(
                    "MESH_NON_FINITE_GEOMETRY",
                    "error",
                    "The mesh contains invalid coordinates and cannot be exported safely.",
                    {},
                )
            )

        if any(value <= 0 for value in dimensions):
            findings.append(
                MeshFinding(
                    "MESH_ZERO_DIMENSION",
                    "error",
                    "The model is flat or collapsed along at least one axis.",
                    {"dimensionsMm": dimensions},
                )
            )

        edge_counts: Counter[tuple[int, int]] = Counter()
        for face in mesh.faces.tolist():
            a, b, c = (int(index) for index in face)
            edge_counts.update(
                (
                    tuple(sorted((a, b))),
                    tuple(sorted((b, c))),
                    tuple(sorted((c, a))),
                )
            )
        boundary_edge_count = sum(count == 1 for count in edge_counts.values())
        non_manifold_edge_count = sum(count > 2 for count in edge_counts.values())
        manifold = non_manifold_edge_count == 0

        if boundary_edge_count:
            findings.append(
                MeshFinding(
                    "MESH_OPEN_BOUNDARIES",
                    "warning",
                    "The model has open boundary edges; slicers may treat it as a surface instead of a solid.",
                    {"boundaryEdgeCount": boundary_edge_count},
                )
            )
        if non_manifold_edge_count:
            findings.append(
                MeshFinding(
                    "MESH_NON_MANIFOLD",
                    "warning",
                    "Some edges belong to more than two faces, which can create ambiguous print geometry.",
                    {"nonManifoldEdgeCount": non_manifold_edge_count},
                )
            )

        area_factor = length_factor * length_factor
        areas = [float(value) * area_factor for value in mesh.area_faces]
        degenerate_face_count = sum((not math.isfinite(area)) or area <= 1e-12 for area in areas)
        if degenerate_face_count:
            findings.append(
                MeshFinding(
                    "MESH_DEGENERATE_FACES",
                    "warning",
                    "The mesh contains zero-area or invalid triangles that should be repaired later.",
                    {"degenerateFaceCount": degenerate_face_count},
                )
            )

        component_count = len(mesh.split(only_watertight=False))  # type: ignore[no-untyped-call]
        if component_count > 1:
            findings.append(
                MeshFinding(
                    "MESH_DISCONNECTED_COMPONENTS",
                    "warning",
                    "The generated model contains disconnected parts; verify that floating geometry is intentional.",
                    {"componentCount": component_count},
                )
            )

        watertight = bool(mesh.is_watertight)
        if not watertight and boundary_edge_count == 0:
            findings.append(
                MeshFinding(
                    "MESH_NOT_WATERTIGHT",
                    "warning",
                    "The model does not form a closed solid and may need repair before printing.",
                    {},
                )
            )

        winding_consistent = bool(mesh.is_winding_consistent)
        if not winding_consistent:
            findings.append(
                MeshFinding(
                    "MESH_WINDING_INCONSISTENT",
                    "warning",
                    "Face orientation is inconsistent, which can cause inside/outside ambiguity.",
                    {},
                )
            )

        normals_finite = all(
            math.isfinite(float(component))
            for normal in mesh.face_normals
            for component in normal
        )
        if not normals_finite:
            findings.append(
                MeshFinding(
                    "MESH_INVALID_NORMALS",
                    "error",
                    "The model contains invalid face normals.",
                    {},
                )
            )

        volume_mm3: float | None = None
        if watertight:
            volume_mm3 = float(mesh.volume) * (length_factor**3)
            if not math.isfinite(volume_mm3) or volume_mm3 <= 0:
                findings.append(
                    MeshFinding(
                        "MESH_INVALID_VOLUME",
                        "error",
                        "The closed mesh has zero, negative or invalid volume.",
                        {"volumeMm3": volume_mm3},
                    )
                )

        export_blocked = any(finding.severity == "error" for finding in findings)
        duration_ms = (time.perf_counter() - started) * 1000
        return MeshValidationReport(
            valid_mesh=not export_blocked,
            export_blocked=export_blocked,
            vertex_count=vertex_count,
            triangle_count=triangle_count,
            component_count=component_count,
            bounds_mm={"min": bounds_raw[0], "max": bounds_raw[1]},
            dimensions_mm=dimensions,
            watertight=watertight,
            manifold=manifold,
            boundary_edge_count=boundary_edge_count,
            non_manifold_edge_count=non_manifold_edge_count,
            degenerate_face_count=degenerate_face_count,
            winding_consistent=winding_consistent,
            volume_mm3=volume_mm3,
            duration_ms=duration_ms,
            findings=tuple(findings),
        )

    @staticmethod
    def _length_factor_to_mm(path: Path) -> float:
        # glTF 2.0 defines linear distances in meters. ARTIFEX canonical geometry is millimeters.
        return 1000.0 if path.suffix.lower() in {".glb", ".gltf"} else 1.0

    @staticmethod
    def _invalid(
        started: float,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> MeshValidationReport:
        return MeshValidationReport(
            valid_mesh=False,
            export_blocked=True,
            vertex_count=0,
            triangle_count=0,
            component_count=0,
            bounds_mm=None,
            dimensions_mm=None,
            watertight=None,
            manifold=None,
            boundary_edge_count=None,
            non_manifold_edge_count=None,
            degenerate_face_count=None,
            winding_consistent=None,
            volume_mm3=None,
            duration_ms=(time.perf_counter() - started) * 1000,
            findings=(MeshFinding(code, "error", message, details or {}),),
        )
