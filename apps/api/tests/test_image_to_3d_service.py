from artifex_api.image_to_3d import GenerationRequest, ImageAssetRef, ImageTo3DService
from artifex_api.image_to_3d.service import UnknownImageTo3DProviderError
from artifex_api.image_to_3d.testing import MockImageTo3DProvider


def test_default_provider_generates_normalized_result() -> None:
    service = ImageTo3DService({"mock": MockImageTo3DProvider()}, default_provider="mock")

    result = service.generate(
        GenerationRequest(
            source_image=ImageAssetRef(asset_id="image-1", media_type="image/png")
        )
    )

    assert result.mesh_asset.asset_id == "mesh-test"
    assert result.mesh_asset.media_type == "model/gltf-binary"
    assert result.provenance.provider == "mock"
    assert service.available_providers == ("mock",)


def test_unknown_provider_is_rejected() -> None:
    service = ImageTo3DService({"mock": MockImageTo3DProvider()}, default_provider="mock")

    try:
        service.generate(
            GenerationRequest(
                source_image=ImageAssetRef(asset_id="image-1", media_type="image/png")
            ),
            provider_id="missing",
        )
    except UnknownImageTo3DProviderError as error:
        assert str(error) == "missing"
    else:
        raise AssertionError("Unknown provider should be rejected")
