from __future__ import annotations

import mimetypes

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from artifex_api.image_to_3d.preprocessing import FileAssetStore

router = APIRouter(prefix="/v1/assets", tags=["assets"])
_store = FileAssetStore()


@router.get("/{asset_id}", response_class=FileResponse)
def get_asset(asset_id: str) -> FileResponse:
    if not asset_id.startswith("asset_") or not asset_id.replace("_", "").isalnum():
        raise HTTPException(status_code=404, detail={"code": "ASSET_NOT_FOUND"})

    try:
        path = _store.resolve(asset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "ASSET_NOT_FOUND"}) from exc

    media_type, _ = mimetypes.guess_type(path.name)
    if path.suffix.lower() == ".glb":
        media_type = "model/gltf-binary"
    return FileResponse(path, media_type=media_type or "application/octet-stream", filename=path.name)
