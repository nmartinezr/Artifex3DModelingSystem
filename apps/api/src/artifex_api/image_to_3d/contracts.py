from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class GenerationErrorCode(str, Enum):
    INVALID_INPUT = "IMAGE_TO_3D_INVALID_INPUT"
    PROVIDER_UNAVAILABLE = "IMAGE_TO_3D_PROVIDER_UNAVAILABLE"
    TIMEOUT = "IMAGE_TO_3D_TIMEOUT"
    CANCELLED = "IMAGE_TO_3D_CANCELLED"
    RESOURCE_EXHAUSTED = "IMAGE_TO_3D_RESOURCE_EXHAUSTED"
    INVALID_OUTPUT = "IMAGE_TO_3D_INVALID_OUTPUT"
    GENERATION_FAILED = "IMAGE_TO_3D_GENERATION_FAILED"


@dataclass(frozen=True)
class ImageAssetRef:
    asset_id: str
    media_type: str


@dataclass(frozen=True)
class GeneratedAssetRef:
    asset_id: str
    media_type: str
    role: str


@dataclass(frozen=True)
class GenerationOptions:
    seed: int | None = None
    quality: str = "balanced"
    generate_texture: bool = True
    provider_options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationRequest:
    source_image: ImageAssetRef
    options: GenerationOptions = field(default_factory=GenerationOptions)


@dataclass(frozen=True)
class GenerationDiagnostic:
    code: str
    severity: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationProvenance:
    provider: str
    model: str
    model_version: str | None
    parameters: Mapping[str, Any]
    processing_time_ms: float


@dataclass(frozen=True)
class GenerationResult:
    mesh_asset: GeneratedAssetRef
    texture_assets: Sequence[GeneratedAssetRef]
    provenance: GenerationProvenance
    diagnostics: Sequence[GenerationDiagnostic] = ()
    project_object: Mapping[str, Any] | None = None


class ImageTo3DProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def generate(self, request: GenerationRequest) -> GenerationResult: ...

    def cancel(self, generation_id: str) -> None: ...
