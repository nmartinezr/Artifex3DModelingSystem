from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    GeneratedAssetRef,
    GenerationProvenance,
    GenerationRequest,
    GenerationResult,
)


@dataclass
class MockImageTo3DProvider:
    provider_id: str = "mock"
    mesh_asset_id: str = "mesh-test"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        return GenerationResult(
            mesh_asset=GeneratedAssetRef(
                asset_id=self.mesh_asset_id,
                media_type="model/gltf-binary",
                role="mesh",
            ),
            texture_assets=(),
            provenance=GenerationProvenance(
                provider=self.provider_id,
                model="deterministic-fixture",
                model_version="1",
                parameters={"quality": request.options.quality},
                processing_time_ms=0.0,
            ),
        )

    def cancel(self, generation_id: str) -> None:
        return None
