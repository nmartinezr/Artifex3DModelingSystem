from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import uuid4

from .contracts import (
    GeneratedAssetRef,
    GenerationDiagnostic,
    GenerationErrorCode,
    GenerationProvenance,
    GenerationRequest,
    GenerationResult,
)
from .preprocessing import FileAssetStore


class TrellisProviderError(RuntimeError):
    def __init__(self, code: GenerationErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class TrellisProvider:
    """TRELLIS adapter executed through an isolated sidecar/runner command."""

    provider_id = "trellis"

    def __init__(
        self,
        store: FileAssetStore | None = None,
        command: str | None = None,
        model: str = "microsoft/TRELLIS-image-large",
        model_version: str | None = None,
        timeout_seconds: float = 300.0,
    ) -> None:
        self._store = store or FileAssetStore()
        self._command = command or os.getenv("ARTIFEX_TRELLIS_COMMAND")
        self._model = model
        self._model_version = model_version
        self._timeout_seconds = timeout_seconds

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self._command:
            raise TrellisProviderError(
                GenerationErrorCode.PROVIDER_UNAVAILABLE,
                "TRELLIS runner is not configured. Set ARTIFEX_TRELLIS_COMMAND.",
            )

        try:
            source_path = self._store.resolve(request.source_image.asset_id)
        except FileNotFoundError as exc:
            raise TrellisProviderError(
                GenerationErrorCode.INVALID_INPUT,
                f"Input asset was not found: {request.source_image.asset_id}",
            ) from exc

        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="artifex-trellis-") as temp_dir:
            work_dir = Path(temp_dir)
            output_dir = work_dir / "output"
            output_dir.mkdir()
            request_path = work_dir / "request.json"
            request_path.write_text(
                json.dumps(
                    {
                        "inputPath": str(source_path.resolve()),
                        "outputDirectory": str(output_dir.resolve()),
                        "model": self._model,
                        "modelVersion": self._model_version,
                        "seed": request.options.seed,
                        "quality": request.options.quality,
                        "generateTexture": request.options.generate_texture,
                        "providerOptions": dict(request.options.provider_options),
                        "outputConventions": {
                            "unit": "mm",
                            "handedness": "right",
                            "upAxis": "Z",
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            command = [*shlex.split(self._command), "--request", str(request_path)]
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise TrellisProviderError(
                    GenerationErrorCode.TIMEOUT,
                    f"TRELLIS generation exceeded {self._timeout_seconds:g} seconds",
                ) from exc
            except OSError as exc:
                raise TrellisProviderError(
                    GenerationErrorCode.PROVIDER_UNAVAILABLE,
                    "TRELLIS runner could not be started",
                ) from exc

            if completed.returncode != 0:
                stderr = completed.stderr.strip()
                lowered = stderr.lower()
                code = (
                    GenerationErrorCode.RESOURCE_EXHAUSTED
                    if completed.returncode == 137
                    or "out of memory" in lowered
                    or "cuda oom" in lowered
                    else GenerationErrorCode.GENERATION_FAILED
                )
                raise TrellisProviderError(code, stderr or "TRELLIS runner failed")

            manifest_path = output_dir / "result.json"
            if not manifest_path.is_file():
                raise TrellisProviderError(
                    GenerationErrorCode.INVALID_OUTPUT,
                    "TRELLIS runner did not produce result.json",
                )

            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                result = self._normalize_result(manifest, output_dir, request)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise TrellisProviderError(
                    GenerationErrorCode.INVALID_OUTPUT,
                    "TRELLIS result manifest is invalid",
                ) from exc

        duration_ms = (time.perf_counter() - started) * 1000
        return GenerationResult(
            mesh_asset=result["mesh_asset"],
            texture_assets=result["texture_assets"],
            provenance=GenerationProvenance(
                provider=self.provider_id,
                model=self._model,
                model_version=self._model_version,
                parameters={
                    "seed": request.options.seed,
                    "quality": request.options.quality,
                    "generateTexture": request.options.generate_texture,
                    **dict(request.options.provider_options),
                },
                processing_time_ms=duration_ms,
            ),
            diagnostics=(
                GenerationDiagnostic(
                    code="TRELLIS_GENERATION_COMPLETED",
                    severity="info",
                    message="TRELLIS generation completed",
                    details={"durationMs": round(duration_ms, 3)},
                ),
            ),
            project_object=result["project_object"],
        )

    def cancel(self, generation_id: str) -> None:
        # The synchronous sidecar contract currently relies on request timeout/worker cancellation.
        # The method remains present so the provider satisfies the stable application contract.
        return None

    def _normalize_result(
        self,
        manifest: Mapping[str, Any],
        output_dir: Path,
        request: GenerationRequest,
    ) -> dict[str, Any]:
        conventions = manifest["conventions"]
        if conventions != {"unit": "mm", "handedness": "right", "upAxis": "Z"}:
            raise ValueError("Runner output is not normalized to ARTIFEX conventions")

        mesh = manifest["mesh"]
        mesh_path = self._safe_output_path(output_dir, mesh["path"])
        mesh_media_type = str(mesh.get("mediaType", "model/gltf-binary"))
        stored_mesh = self._store.save(mesh_path.read_bytes(), mesh_media_type, mesh_path.suffix)
        mesh_asset = GeneratedAssetRef(stored_mesh.asset_id, mesh_media_type, "mesh")

        texture_assets: list[GeneratedAssetRef] = []
        for texture in manifest.get("textures", []):
            texture_path = self._safe_output_path(output_dir, texture["path"])
            media_type = str(texture.get("mediaType", "image/png"))
            stored = self._store.save(texture_path.read_bytes(), media_type, texture_path.suffix)
            texture_assets.append(GeneratedAssetRef(stored.asset_id, media_type, "texture"))

        triangle_count = int(mesh["triangleCount"])
        vertex_count = int(mesh["vertexCount"])
        bounds = mesh["boundsMm"]
        minimum = self._vector(bounds["min"])
        maximum = self._vector(bounds["max"])
        object_id = f"object_{uuid4().hex}"

        project_object: dict[str, Any] = {
            "objectId": object_id,
            "name": str(manifest.get("name", "Generated model")),
            "visible": True,
            "transform": {
                "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
            },
            "mesh": {
                "asset": {
                    "assetId": stored_mesh.asset_id,
                    "mediaType": mesh_media_type,
                    "checksum": stored_mesh.sha256,
                    "byteLength": stored_mesh.path.stat().st_size,
                },
                "triangleCount": triangle_count,
                "vertexCount": vertex_count,
                "bounds": {"min": minimum, "max": maximum},
            },
            "metadata": {
                "source": "image-to-3d",
                "provider": self.provider_id,
                "model": self._model,
                "sourceImageAssetId": request.source_image.asset_id,
            },
        }
        return {
            "mesh_asset": mesh_asset,
            "texture_assets": tuple(texture_assets),
            "project_object": project_object,
        }

    @staticmethod
    def _safe_output_path(output_dir: Path, relative_path: str) -> Path:
        candidate = (output_dir / relative_path).resolve()
        root = output_dir.resolve()
        if root not in candidate.parents or not candidate.is_file():
            raise ValueError("Invalid output asset path")
        return candidate

    @staticmethod
    def _vector(values: Any) -> dict[str, float]:
        if not isinstance(values, list) or len(values) != 3:
            raise ValueError("Expected 3D vector")
        return {"x": float(values[0]), "y": float(values[1]), "z": float(values[2])}
