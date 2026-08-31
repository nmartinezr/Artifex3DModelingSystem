from __future__ import annotations

import os

from .contracts import GenerationDiagnostic, GenerationRequest, GenerationResult
from .preprocessing import FileAssetStore
from .trellis_provider import TrellisProvider, TrellisProviderError


class RunnerBackedProvider(TrellisProvider):
    """Reuse the stable ARTIFEX runner manifest contract for additional Image → 3D engines."""

    def __init__(
        self,
        provider_id: str,
        display_name: str,
        env_var: str,
        model: str,
        store: FileAssetStore | None = None,
        timeout_seconds: float = 300.0,
    ) -> None:
        self.provider_id = provider_id
        self._display_name = display_name
        self._env_var = env_var
        configured = os.getenv(env_var)
        super().__init__(
            store=store,
            command=configured or "__artifex_provider_not_configured__",
            model=model,
            timeout_seconds=timeout_seconds,
        )
        self._command = configured

    def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            result = super().generate(request)
        except TrellisProviderError as exc:
            message = exc.message.replace("TRELLIS", self._display_name)
            if "runner is not configured" in message:
                message = f"{self._display_name} runner is not configured. Set {self._env_var}."
            raise TrellisProviderError(exc.code, message) from exc

        return GenerationResult(
            mesh_asset=result.mesh_asset,
            texture_assets=result.texture_assets,
            provenance=result.provenance,
            diagnostics=(
                GenerationDiagnostic(
                    code=f"{self.provider_id.upper().replace('-', '_')}_GENERATION_COMPLETED",
                    severity="info",
                    message=f"{self._display_name} generation completed",
                    details={
                        "durationMs": round(result.provenance.processing_time_ms, 3),
                        "runnerEnvironmentVariable": self._env_var,
                    },
                ),
            ),
            project_object=result.project_object,
        )


class StableFast3DProvider(RunnerBackedProvider):
    def __init__(self, store: FileAssetStore | None = None) -> None:
        timeout_seconds = float(os.getenv("ARTIFEX_STABLE_FAST_3D_TIMEOUT_SECONDS", "900"))
        super().__init__(
            provider_id="stable-fast-3d",
            display_name="Stable Fast 3D",
            env_var="ARTIFEX_STABLE_FAST_3D_COMMAND",
            model="stabilityai/stable-fast-3d",
            store=store,
            timeout_seconds=timeout_seconds,
        )


class Spar3DProvider(RunnerBackedProvider):
    def __init__(self, store: FileAssetStore | None = None) -> None:
        super().__init__(
            provider_id="spar3d",
            display_name="SPAR3D",
            env_var="ARTIFEX_SPAR3D_COMMAND",
            model="stabilityai/stable-point-aware-3d",
            store=store,
        )


class Hunyuan3DProvider(RunnerBackedProvider):
    def __init__(self, store: FileAssetStore | None = None) -> None:
        super().__init__(
            provider_id="hunyuan3d",
            display_name="Hunyuan3D",
            env_var="ARTIFEX_HUNYUAN3D_COMMAND",
            model="tencent/Hunyuan3D-2",
            store=store,
            timeout_seconds=600.0,
        )
