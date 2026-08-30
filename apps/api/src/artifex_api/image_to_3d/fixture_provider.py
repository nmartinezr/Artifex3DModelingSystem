from __future__ import annotations

from uuid import uuid4

from .contracts import (
    GeneratedAssetRef,
    GenerationDiagnostic,
    GenerationProvenance,
    GenerationRequest,
    GenerationResult,
)
from .fixture_glb import create_fixture_cube_glb
from .preprocessing import FileAssetStore


class FixtureImageTo3DProvider:
    """Local development provider that emits a real GLB without GPU/model dependencies."""

    provider_id = "fixture"

    def __init__(self, store: FileAssetStore | None = None) -> None:
        self._store = store or FileAssetStore()

    def generate(self, request: GenerationRequest) -> GenerationResult:
        size_mm = 40.0
        content = create_fixture_cube_glb(size_mm=size_mm)
        stored = self._store.save(content, "model/gltf-binary", ".glb")
        half = size_mm / 2.0
        object_id = f"object_{uuid4().hex}"

        return GenerationResult(
            mesh_asset=GeneratedAssetRef(stored.asset_id, "model/gltf-binary", "mesh"),
            texture_assets=(),
            provenance=GenerationProvenance(
                provider=self.provider_id,
                model="deterministic-cube",
                model_version="1",
                parameters={"quality": request.options.quality, "sizeMm": size_mm},
                processing_time_ms=0.0,
            ),
            diagnostics=(
                GenerationDiagnostic(
                    code="FIXTURE_GENERATION_COMPLETED",
                    severity="info",
                    message="Deterministic development GLB generated",
                    details={"triangleCount": 12, "vertexCount": 24},
                ),
            ),
            project_object={
                "objectId": object_id,
                "name": "ARTIFEX Fixture Cube",
                "visible": True,
                "transform": {
                    "translation": {"x": 0.0, "y": 0.0, "z": half},
                    "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                    "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
                },
                "mesh": {
                    "asset": {
                        "assetId": stored.asset_id,
                        "mediaType": stored.media_type,
                        "checksum": stored.sha256,
                        "byteLength": len(content),
                    },
                    "triangleCount": 12,
                    "vertexCount": 24,
                    "bounds": {
                        "min": {"x": -half, "y": -half, "z": -half},
                        "max": {"x": half, "y": half, "z": half},
                    },
                },
                "metadata": {
                    "source": "image-to-3d-development-fixture",
                    "provider": self.provider_id,
                    "sourceImageAssetId": request.source_image.asset_id,
                },
            },
        )

    def cancel(self, generation_id: str) -> None:
        return None
