from __future__ import annotations

from typing import Annotated, Any

from artifex_geometry import TrimeshMeshValidator
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from .contracts import GenerationOptions, GenerationRequest, ImageAssetRef
from .fixture_provider import FixtureImageTo3DProvider
from .preprocessing import FileAssetStore, ImagePreprocessingError, ImagePreprocessor
from .service import ImageTo3DService, UnknownImageTo3DProviderError
from .trellis_provider import TrellisProvider, TrellisProviderError

router = APIRouter(prefix="/v1/image-to-3d", tags=["image-to-3d"])
_preprocessor = ImagePreprocessor()
_asset_store = FileAssetStore()
_validator = TrimeshMeshValidator()
_service = ImageTo3DService(
    providers={
        "fixture": FixtureImageTo3DProvider(),
        "trellis": TrellisProvider(),
    },
    default_provider="fixture",
)


class GenerateImageResponse(BaseModel):
    original_asset_id: str
    processed_asset_id: str
    mesh_asset_id: str
    mesh_media_type: str
    provider: str
    model: str
    processing_time_ms: float
    project_object: dict[str, Any] | None
    analysis: dict[str, Any]


@router.post("/generate", response_model=GenerateImageResponse)
async def generate_from_image(
    file: Annotated[UploadFile, File()],
    provider: Annotated[str, Query()] = "fixture",
) -> GenerateImageResponse:
    media_type = file.content_type or "application/octet-stream"
    content = await file.read()

    try:
        preprocessed = _preprocessor.process(content, media_type)
        generated = _service.generate(
            GenerationRequest(
                source_image=ImageAssetRef(
                    asset_id=preprocessed.processed.asset_id,
                    media_type=preprocessed.processed.media_type,
                ),
                options=GenerationOptions(),
            ),
            provider_id=provider,
        )
    except ImagePreprocessingError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    except UnknownImageTo3DProviderError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "IMAGE_TO_3D_PROVIDER_UNKNOWN", "message": str(exc)},
        ) from exc
    except TrellisProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": exc.code.value, "message": exc.message},
        ) from exc

    mesh_path = _asset_store.resolve(generated.mesh_asset.asset_id)
    validation = _validator.validate_path(mesh_path)
    finding_penalty = sum(30 if item.severity == "error" else 10 for item in validation.findings)
    analysis: dict[str, Any] = {
        "score": max(0, 100 - finding_penalty),
        "findings": [
            {
                "code": item.code,
                "severity": item.severity,
                "message": item.message,
                "details": item.details,
            }
            for item in validation.findings
        ],
        "metrics": {
            "vertexCount": validation.vertex_count,
            "triangleCount": validation.triangle_count,
            "componentCount": validation.component_count,
            "boundsMm": validation.bounds_mm,
            "dimensionsMm": validation.dimensions_mm,
            "watertight": validation.watertight,
            "manifold": validation.manifold,
            "boundaryEdgeCount": validation.boundary_edge_count,
            "nonManifoldEdgeCount": validation.non_manifold_edge_count,
            "degenerateFaceCount": validation.degenerate_face_count,
            "windingConsistent": validation.winding_consistent,
            "volumeMm3": validation.volume_mm3,
            "durationMs": round(validation.duration_ms, 3),
        },
        "exportBlocked": validation.export_blocked,
    }

    project_object = dict(generated.project_object) if generated.project_object is not None else None
    return GenerateImageResponse(
        original_asset_id=preprocessed.original.asset_id,
        processed_asset_id=preprocessed.processed.asset_id,
        mesh_asset_id=generated.mesh_asset.asset_id,
        mesh_media_type=generated.mesh_asset.media_type,
        provider=generated.provenance.provider,
        model=generated.provenance.model,
        processing_time_ms=round(generated.provenance.processing_time_ms, 3),
        project_object=project_object,
        analysis=analysis,
    )
