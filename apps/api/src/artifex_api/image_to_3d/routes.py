from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from .preprocessing import ImagePreprocessingError, ImagePreprocessor

router = APIRouter(prefix="/v1/images", tags=["image-to-3d"])
_preprocessor = ImagePreprocessor()


class AssetResponse(BaseModel):
    asset_id: str
    media_type: str
    sha256: str


class DiagnosticResponse(BaseModel):
    stage: str
    duration_ms: float
    message: str


class PreprocessImageResponse(BaseModel):
    original: AssetResponse
    processed: AssetResponse
    width: int
    height: int
    diagnostics: list[DiagnosticResponse]


@router.post("/preprocess", response_model=PreprocessImageResponse)
async def preprocess_image(file: UploadFile = File(...)) -> PreprocessImageResponse:
    media_type = file.content_type or "application/octet-stream"
    content = await file.read()
    try:
        result = _preprocessor.process(content, media_type)
    except ImagePreprocessingError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    return PreprocessImageResponse(
        original=AssetResponse(
            asset_id=result.original.asset_id,
            media_type=result.original.media_type,
            sha256=result.original.sha256,
        ),
        processed=AssetResponse(
            asset_id=result.processed.asset_id,
            media_type=result.processed.media_type,
            sha256=result.processed.sha256,
        ),
        width=result.width,
        height=result.height,
        diagnostics=[
            DiagnosticResponse(
                stage=item.stage,
                duration_ms=round(item.duration_ms, 3),
                message=item.message,
            )
            for item in result.diagnostics
        ],
    )
