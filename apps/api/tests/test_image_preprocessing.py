from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from artifex_api.image_to_3d.preprocessing import (
    FileAssetStore,
    ImagePreprocessingError,
    ImagePreprocessor,
)


def image_bytes(format_name: str = "PNG", mode: str = "RGB") -> bytes:
    image = Image.new(mode, (8, 6), (255, 255, 255, 255) if mode == "RGBA" else "white")
    output = io.BytesIO()
    image.save(output, format=format_name)
    return output.getvalue()


def test_png_is_preserved_and_normalized(tmp_path: Path) -> None:
    processor = ImagePreprocessor(store=FileAssetStore(tmp_path))
    result = processor.process(image_bytes(), "image/png")

    assert result.original.path.exists()
    assert result.processed.path.exists()
    assert result.processed.media_type == "image/png"
    assert result.width == 8
    assert result.height == 6
    assert result.original.asset_id != result.processed.asset_id
    assert len(result.diagnostics) == 2


def test_transparent_png_is_supported(tmp_path: Path) -> None:
    processor = ImagePreprocessor(store=FileAssetStore(tmp_path))
    result = processor.process(image_bytes(mode="RGBA"), "image/png")
    with Image.open(result.processed.path) as processed:
        assert processed.mode == "RGBA"


def test_unsupported_media_type_is_rejected(tmp_path: Path) -> None:
    processor = ImagePreprocessor(store=FileAssetStore(tmp_path))
    with pytest.raises(ImagePreprocessingError) as exc:
        processor.process(b"abc", "image/gif")
    assert exc.value.code == "IMAGE_UNSUPPORTED_FORMAT"


def test_corrupt_image_is_rejected(tmp_path: Path) -> None:
    processor = ImagePreprocessor(store=FileAssetStore(tmp_path))
    with pytest.raises(ImagePreprocessingError) as exc:
        processor.process(b"not-an-image", "image/png")
    assert exc.value.code == "IMAGE_INVALID"


def test_oversized_input_is_rejected(tmp_path: Path) -> None:
    processor = ImagePreprocessor(store=FileAssetStore(tmp_path))
    with pytest.raises(ImagePreprocessingError) as exc:
        processor.process(b"x" * (15 * 1024 * 1024 + 1), "image/png")
    assert exc.value.code == "IMAGE_TOO_LARGE"


class FailingRemover:
    def remove(self, image: Image.Image) -> Image.Image:
        raise RuntimeError("boom")


def test_background_removal_failure_is_normalized(tmp_path: Path) -> None:
    processor = ImagePreprocessor(
        store=FileAssetStore(tmp_path),
        background_remover=FailingRemover(),
    )
    with pytest.raises(ImagePreprocessingError) as exc:
        processor.process(image_bytes(), "image/png")
    assert exc.value.code == "BACKGROUND_REMOVAL_FAILED"
