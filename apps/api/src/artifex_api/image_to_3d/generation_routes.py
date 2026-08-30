from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from .contracts import GenerationOptions, GenerationRequest, ImageAssetRef
from .fixture_provider import FixtureImageTo3DProvider
from .preprocessing import ImagePreprocessingError, ImagePreprocessor
from .service import ImageTo3DService, UnknownImageTo3DProviderError
from .trellis_provider import TrellisProvider, TrellisProviderError

router = APIRouter(prefix="/v1/image-to-3d", tags=["image-to-3d"])
_preprocessor = ImagePreprocessor()
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
    )
