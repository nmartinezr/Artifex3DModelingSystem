from __future__ import annotations

import time
from typing import Annotated, Any
from uuid import uuid4

from artifex_geometry import TrimeshMeshValidator
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from .contracts import GenerationOptions, GenerationRequest, ImageAssetRef
from .diagnostics import GenerationTelemetryRecord, JsonLogTelemetrySink, sanitized_parameters
from .fixture_provider import FixtureImageTo3DProvider
from .preprocessing import FileAssetStore, ImagePreprocessingError, ImagePreprocessor
from .provider_variants import Hunyuan3DProvider, Spar3DProvider, StableFast3DProvider
from .service import ImageTo3DService, UnknownImageTo3DProviderError
from .style_preprocessing import (
    RunnerStylePreprocessor,
    StylePreprocessingError,
    UnknownStylePresetError,
    resolve_style_preset,
)
from .trellis_provider import TrellisProvider, TrellisProviderError

router = APIRouter(prefix="/v1/image-to-3d", tags=["image-to-3d"])
_preprocessor = ImagePreprocessor()
_style_preprocessor = RunnerStylePreprocessor()
_asset_store = FileAssetStore()
_validator = TrimeshMeshValidator()
_telemetry = JsonLogTelemetrySink()
_service = ImageTo3DService(
    providers={
        "fixture": FixtureImageTo3DProvider(),
        "trellis": TrellisProvider(),
        "stable-fast-3d": StableFast3DProvider(),
        "spar3d": Spar3DProvider(),
        "hunyuan3d": Hunyuan3DProvider(),
    },
    default_provider="fixture",
)


class GenerateImageResponse(BaseModel):
    correlation_id: str
    original_asset_id: str
    processed_asset_id: str
    styled_asset_id: str
    style: str
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
    style: Annotated[str, Query()] = "none",
) -> GenerateImageResponse:
    started = time.perf_counter()
    correlation_id = f"gen_{uuid4().hex}"
    media_type = file.content_type or "application/octet-stream"
    content = await file.read()
    preprocessing_duration_ms = 0.0
    generation_duration_ms = 0.0

    try:
        preset = resolve_style_preset(style)
        preprocessing_started = time.perf_counter()
        preprocessed = _preprocessor.process(content, media_type)
        styled = _style_preprocessor.stylize(preprocessed.processed, preset)
        preprocessing_duration_ms = (time.perf_counter() - preprocessing_started) * 1000

        generation_started = time.perf_counter()
        generated = _service.generate(
            GenerationRequest(
                source_image=ImageAssetRef(asset_id=styled.asset_id, media_type=styled.media_type),
                options=GenerationOptions(provider_options={"style": preset.style_id}),
            ),
            provider_id=provider,
        )
        generation_duration_ms = (time.perf_counter() - generation_started) * 1000
    except UnknownStylePresetError as exc:
        _emit_failure(
            correlation_id,
            provider,
            started,
            preprocessing_duration_ms,
            generation_duration_ms,
            "IMAGE_TO_3D_STYLE_UNKNOWN",
        )
        raise HTTPException(
            status_code=400,
            detail={
                "code": "IMAGE_TO_3D_STYLE_UNKNOWN",
                "message": f"Unknown style preset: {exc}",
                "correlationId": correlation_id,
            },
        ) from exc
    except StylePreprocessingError as exc:
        _emit_failure(
            correlation_id,
            provider,
            started,
            preprocessing_duration_ms,
            generation_duration_ms,
            "IMAGE_TO_3D_STYLE_UNAVAILABLE",
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": "IMAGE_TO_3D_STYLE_UNAVAILABLE",
                "message": str(exc),
                "correlationId": correlation_id,
            },
        ) from exc
    except ImagePreprocessingError as exc:
        _emit_failure(
            correlation_id,
            provider,
            started,
            preprocessing_duration_ms,
            generation_duration_ms,
            exc.code,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": exc.code, "message": exc.message, "correlationId": correlation_id},
        ) from exc
    except UnknownImageTo3DProviderError as exc:
        _emit_failure(
            correlation_id,
            provider,
            started,
            preprocessing_duration_ms,
            generation_duration_ms,
            "IMAGE_TO_3D_PROVIDER_UNKNOWN",
        )
        raise HTTPException(
            status_code=400,
            detail={
                "code": "IMAGE_TO_3D_PROVIDER_UNKNOWN",
                "message": str(exc),
                "correlationId": correlation_id,
            },
        ) from exc
    except TrellisProviderError as exc:
        _emit_failure(
            correlation_id,
            provider,
            started,
            preprocessing_duration_ms,
            generation_duration_ms,
            exc.code.value,
        )
        raise HTTPException(
            status_code=503,
            detail={"code": exc.code.value, "message": exc.message, "correlationId": correlation_id},
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

    _telemetry.emit(
        GenerationTelemetryRecord(
            correlation_id=correlation_id,
            provider=generated.provenance.provider,
            model=generated.provenance.model,
            model_version=generated.provenance.model_version,
            parameters=sanitized_parameters(generated.provenance.parameters),
            input_width=preprocessed.width,
            input_height=preprocessed.height,
            preprocessing_duration_ms=round(preprocessing_duration_ms, 3),
            generation_duration_ms=round(generation_duration_ms, 3),
            validation_duration_ms=round(validation.duration_ms, 3),
            total_duration_ms=round((time.perf_counter() - started) * 1000, 3),
            vertex_count=validation.vertex_count,
            triangle_count=validation.triangle_count,
            component_count=validation.component_count,
            validation_summary={
                "score": analysis["score"],
                "exportBlocked": validation.export_blocked,
                "findingCodes": [item.code for item in validation.findings],
                "style": preset.style_id,
            },
        )
    )

    project_object = dict(generated.project_object) if generated.project_object is not None else None
    return GenerateImageResponse(
        correlation_id=correlation_id,
        original_asset_id=preprocessed.original.asset_id,
        processed_asset_id=preprocessed.processed.asset_id,
        styled_asset_id=styled.asset_id,
        style=preset.style_id,
        mesh_asset_id=generated.mesh_asset.asset_id,
        mesh_media_type=generated.mesh_asset.media_type,
        provider=generated.provenance.provider,
        model=generated.provenance.model,
        processing_time_ms=round(generated.provenance.processing_time_ms, 3),
        project_object=project_object,
        analysis=analysis,
    )


def _emit_failure(
    correlation_id: str,
    provider: str,
    started: float,
    preprocessing_duration_ms: float,
    generation_duration_ms: float,
    error_code: str,
) -> None:
    _telemetry.emit(
        GenerationTelemetryRecord(
            correlation_id=correlation_id,
            provider=provider,
            model=None,
            model_version=None,
            parameters={},
            input_width=None,
            input_height=None,
            preprocessing_duration_ms=round(preprocessing_duration_ms, 3),
            generation_duration_ms=round(generation_duration_ms, 3),
            validation_duration_ms=0.0,
            total_duration_ms=round((time.perf_counter() - started) * 1000, 3),
            vertex_count=None,
            triangle_count=None,
            component_count=None,
            validation_summary={},
            error_code=error_code,
        )
    )
