"""ARTIFEX geometry engine contracts and adapters."""

from .contracts import (
    AssetRef,
    Bounds3D,
    GeometryDiagnostic,
    GeometryEngine,
    GeometryErrorCode,
    GeometryResult,
    MeshMetadata,
)
from .validation import MeshFinding, MeshValidationReport, TrimeshMeshValidator

__all__ = [
    "AssetRef",
    "Bounds3D",
    "GeometryDiagnostic",
    "GeometryEngine",
    "GeometryErrorCode",
    "GeometryResult",
    "MeshFinding",
    "MeshMetadata",
    "MeshValidationReport",
    "TrimeshMeshValidator",
]
