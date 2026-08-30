from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Protocol

logger = logging.getLogger("artifex.image_to_3d")


@dataclass(frozen=True)
class GenerationTelemetryRecord:
    correlation_id: str
    provider: str
    model: str | None
    model_version: str | None
    parameters: Mapping[str, Any]
    input_width: int | None
    input_height: int | None
    preprocessing_duration_ms: float
    generation_duration_ms: float
    validation_duration_ms: float
    total_duration_ms: float
    vertex_count: int | None
    triangle_count: int | None
    component_count: int | None
    validation_summary: Mapping[str, Any]
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TelemetrySink(Protocol):
    def emit(self, record: GenerationTelemetryRecord) -> None: ...


class JsonLogTelemetrySink:
    """Best-effort structured telemetry sink; generation never depends on logging success."""

    def emit(self, record: GenerationTelemetryRecord) -> None:
        try:
            logger.info("image_to_3d_generation %s", json.dumps(record.to_dict(), sort_keys=True))
        except Exception:  # pragma: no cover - telemetry must never break generation
            logger.exception("Failed to emit Image to 3D telemetry")


def sanitized_parameters(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Keep scalar configuration only; never serialize images, paths, tokens or arbitrary payloads."""
    safe: dict[str, Any] = {}
    for key, value in parameters.items():
        normalized = key.lower()
        if any(token in normalized for token in ("image", "path", "token", "secret", "key")):
            continue
        if value is None or isinstance(value, (str, int, float, bool)):
            safe[key] = value
    return safe
