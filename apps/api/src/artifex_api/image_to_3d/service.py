from __future__ import annotations

from collections.abc import Mapping

from .contracts import GenerationRequest, GenerationResult, ImageTo3DProvider


class UnknownImageTo3DProviderError(ValueError):
    pass


class ImageTo3DService:
    def __init__(self, providers: Mapping[str, ImageTo3DProvider], default_provider: str) -> None:
        if default_provider not in providers:
            raise UnknownImageTo3DProviderError(default_provider)
        self._providers = dict(providers)
        self._default_provider = default_provider

    @property
    def available_providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    def generate(
        self,
        request: GenerationRequest,
        provider_id: str | None = None,
    ) -> GenerationResult:
        selected = provider_id or self._default_provider
        provider = self._providers.get(selected)
        if provider is None:
            raise UnknownImageTo3DProviderError(selected)
        return provider.generate(request)
