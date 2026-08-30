from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class GeometryErrorCode(str, Enum):
    INVALID_MESH = "INVALID_MESH"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    GEOMETRY_OPERATION_FAILED = "GEOMETRY_OPERATION_FAILED"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    CUT_NO_INTERSECTION = "CUT_NO_INTERSECTION"
    CUT_CREATES_OPEN_SURFACE = "CUT_CREATES_OPEN_SURFACE"


@dataclass(frozen=True)
class AssetRef:
    asset_id: str
    media_type: str


@dataclass(frozen=True)
class Bounds3D:
    minimum_mm: tuple[float, float, float]
    maximum_mm: tuple[float, float, float]


@dataclass(frozen=True)
class MeshMetadata:
    vertex_count: int
    triangle_count: int
    component_count: int
    bounds: Bounds3D
    watertight: bool | None = None
    manifold: bool | None = None
    volume_mm3: float | None = None


@dataclass(frozen=True)
class GeometryDiagnostic:
    code: str
    severity: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GeometryResult:
    asset: AssetRef | None
    metadata: MeshMetadata | None
    diagnostics: Sequence[GeometryDiagnostic] = ()


class GeometryEngine(Protocol):
    """Provider-neutral boundary for all geometry implementations."""

    def inspect(self, asset: AssetRef) -> GeometryResult: ...

    def transform(
        self,
        asset: AssetRef,
        matrix_4x4: Sequence[Sequence[float]],
    ) -> GeometryResult: ...

    def separate_components(self, asset: AssetRef) -> Sequence[GeometryResult]: ...

    def repair(self, asset: AssetRef, options: Mapping[str, Any]) -> GeometryResult: ...

    def planar_cut(
        self,
        asset: AssetRef,
        plane_origin_mm: tuple[float, float, float],
        plane_normal: tuple[float, float, float],
    ) -> Sequence[GeometryResult]: ...
