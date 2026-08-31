from __future__ import annotations

import pytest

from artifex_api.image_to_3d.contracts import GenerationErrorCode, GenerationRequest, ImageAssetRef
from artifex_api.image_to_3d.provider_variants import (
    Hunyuan3DProvider,
    Spar3DProvider,
    StableFast3DProvider,
)
from artifex_api.image_to_3d.trellis_provider import TrellisProviderError


@pytest.mark.parametrize(
    ("provider", "provider_id", "env_var"),
    [
        (StableFast3DProvider(), "stable-fast-3d", "ARTIFEX_STABLE_FAST_3D_COMMAND"),
        (Spar3DProvider(), "spar3d", "ARTIFEX_SPAR3D_COMMAND"),
        (Hunyuan3DProvider(), "hunyuan3d", "ARTIFEX_HUNYUAN3D_COMMAND"),
    ],
)
def test_unconfigured_provider_has_stable_identity_and_actionable_error(
    monkeypatch: pytest.MonkeyPatch,
    provider: object,
    provider_id: str,
    env_var: str,
) -> None:
    monkeypatch.delenv(env_var, raising=False)
    assert getattr(provider, "provider_id") == provider_id

    request = GenerationRequest(source_image=ImageAssetRef("asset_missing", "image/png"))
    with pytest.raises(TrellisProviderError) as caught:
        getattr(provider, "generate")(request)

    assert caught.value.code == GenerationErrorCode.PROVIDER_UNAVAILABLE
    assert env_var in caught.value.message
    assert "TRELLIS runner is not configured" not in caught.value.message
