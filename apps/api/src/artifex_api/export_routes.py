from __future__ import annotations

from typing import Annotated, Any

from artifex_export import ExportError, ExportFormat, ExportService
from artifex_geometry import TrimeshMeshValidator
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from artifex_api.image_to_3d.preprocessing import FileAssetStore

router = APIRouter(prefix="/v1/exports", tags=["exports"])
_store = FileAssetStore()
_validator = TrimeshMeshValidator()
_exporter = ExportService()


class ExportResponse(BaseModel):
    source_asset_id: str
    export_asset_id: str
    format: str
    media_type: str
    warning: str | None
    validation: dict[str, Any]


@router.post("/{asset_id}", response_model=ExportResponse)
def export_asset(
    asset_id: str,
    format: Annotated[str, Query(pattern="^(glb|stl|3mf)$")] = "3mf",
) -> ExportResponse:
    try:
        source = _store.resolve(asset_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "EXPORT_SOURCE_NOT_FOUND", "message": "Source asset was not found"},
        ) from exc

    validation = _validator.validate_path(source)
    if validation.export_blocked:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "EXPORT_BLOCKED_BY_VALIDATION",
                "message": "Mesh validation found severe geometry errors",
                "findings": [
                    {"code": item.code, "severity": item.severity, "message": item.message}
                    for item in validation.findings
                ],
            },
        )

    export_format = ExportFormat(format)
    try:
        artifact = _exporter.export_path(source, export_format)
    except ExportError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    stored = _store.save(artifact.content, artifact.media_type, artifact.suffix)
    return ExportResponse(
        source_asset_id=asset_id,
        export_asset_id=stored.asset_id,
        format=export_format.value,
        media_type=stored.media_type,
        warning=artifact.warning,
        validation=validation.to_dict(),
    )
