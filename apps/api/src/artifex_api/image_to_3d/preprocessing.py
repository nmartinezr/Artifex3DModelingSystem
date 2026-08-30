from __future__ import annotations

import hashlib
import io
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from PIL import Image, ImageChops, ImageOps, UnidentifiedImageError

SUPPORTED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


class ImagePreprocessingError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class StoredImageAsset:
    asset_id: str
    media_type: str
    path: Path
    sha256: str


@dataclass(frozen=True)
class PreprocessingDiagnostic:
    stage: str
    duration_ms: float
    message: str


@dataclass(frozen=True)
class PreprocessingResult:
    original: StoredImageAsset
    processed: StoredImageAsset
    width: int
    height: int
    diagnostics: tuple[PreprocessingDiagnostic, ...]


class BackgroundRemover(Protocol):
    def remove(self, image: Image.Image) -> Image.Image: ...


class BasicBackgroundRemover:
    """Deterministic baseline remover; replaceable by a model-backed implementation later."""

    def __init__(self, tolerance: int = 24) -> None:
        self._tolerance = tolerance

    def remove(self, image: Image.Image) -> Image.Image:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, rgba.getpixel((0, 0)))
        difference = ImageChops.difference(rgba, background).convert("L")
        mask = difference.point(lambda value: 255 if value > self._tolerance else 0)
        result = rgba.copy()
        result.putalpha(mask)
        return result


class FileAssetStore:
    def __init__(self, root: Path | None = None) -> None:
        configured = os.getenv("ARTIFEX_ASSET_ROOT")
        self.root = root or Path(configured or ".artifex-data/assets")
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, media_type: str, suffix: str) -> StoredImageAsset:
        digest = hashlib.sha256(content).hexdigest()
        asset_id = f"asset_{uuid4().hex}"
        path = self.root / f"{asset_id}{suffix}"
        path.write_bytes(content)
        return StoredImageAsset(asset_id=asset_id, media_type=media_type, path=path, sha256=digest)

    def resolve(self, asset_id: str) -> Path:
        matches = tuple(self.root.glob(f"{asset_id}.*"))
        if len(matches) != 1:
            raise FileNotFoundError(asset_id)
        return matches[0]


class ImagePreprocessor:
    def __init__(
        self,
        store: FileAssetStore | None = None,
        background_remover: BackgroundRemover | None = None,
    ) -> None:
        self._store = store or FileAssetStore()
        self._background_remover = background_remover or BasicBackgroundRemover()

    def process(self, content: bytes, media_type: str) -> PreprocessingResult:
        if media_type not in SUPPORTED_MEDIA_TYPES:
            raise ImagePreprocessingError("IMAGE_UNSUPPORTED_FORMAT", "Unsupported image format")
        if not content:
            raise ImagePreprocessingError("IMAGE_EMPTY", "Image is empty")
        if len(content) > MAX_IMAGE_BYTES:
            raise ImagePreprocessingError("IMAGE_TOO_LARGE", "Image exceeds the 15 MB upload limit")

        suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[media_type]
        original = self._store.save(content, media_type, suffix)

        started = time.perf_counter()
        try:
            with Image.open(io.BytesIO(content)) as source:
                source.verify()
            with Image.open(io.BytesIO(content)) as source:
                image = ImageOps.exif_transpose(source)
                image.load()
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise ImagePreprocessingError(
                        "IMAGE_PIXEL_LIMIT_EXCEEDED",
                        "Image dimensions exceed the processing limit",
                    )
                normalized = image.convert("RGBA")
        except (UnidentifiedImageError, OSError) as exc:
            raise ImagePreprocessingError("IMAGE_INVALID", "Image data is corrupt or invalid") from exc
        decode_ms = (time.perf_counter() - started) * 1000

        started = time.perf_counter()
        try:
            processed_image = self._background_remover.remove(normalized)
        except Exception as exc:
            raise ImagePreprocessingError(
                "BACKGROUND_REMOVAL_FAILED",
                "Background removal failed",
            ) from exc
        removal_ms = (time.perf_counter() - started) * 1000

        output = io.BytesIO()
        processed_image.save(output, format="PNG", optimize=True)
        processed = self._store.save(output.getvalue(), "image/png", ".png")

        return PreprocessingResult(
            original=original,
            processed=processed,
            width=processed_image.width,
            height=processed_image.height,
            diagnostics=(
                PreprocessingDiagnostic("decode-and-orient", decode_ms, "Image decoded and oriented"),
                PreprocessingDiagnostic("background-removal", removal_ms, "Background removal completed"),
            ),
        )
