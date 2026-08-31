from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .preprocessing import FileAssetStore, StoredImageAsset


@dataclass(frozen=True)
class StylePreset:
    style_id: str
    display_name: str
    prompt: str
    negative_prompt: str


STYLE_PRESETS: dict[str, StylePreset] = {
    "none": StylePreset("none", "Original", "", ""),
    "collectible-vinyl": StylePreset(
        "collectible-vinyl",
        "Collectible Vinyl",
        "stylized collectible vinyl figure, oversized head, compact body, simplified facial features, clean silhouette, smooth printable forms, preserve subject identity and clothing cues",
        "brand logos, packaging, text, photorealistic skin pores, thin fragile details, floating accessories",
    ),
    "chibi": StylePreset(
        "chibi",
        "Chibi",
        "chibi character figure, very large head, small body, simplified expressive features, rounded forms, preserve subject identity",
        "text, logos, photorealism, thin fragile geometry",
    ),
    "anime-figure": StylePreset(
        "anime-figure",
        "Anime Figure",
        "anime-inspired collectible figure, clean cel-shaded shapes, expressive face, simplified hair masses, display-figure proportions, preserve identity",
        "text, logos, overly thin hair strands, floating geometry",
    ),
    "cartoon": StylePreset(
        "cartoon",
        "Cartoon",
        "friendly 3D cartoon character, simplified forms, clear silhouette, rounded features, preserve subject identity and recognizable clothing",
        "text, logos, photorealistic noise, tiny fragile details",
    ),
    "miniature": StylePreset(
        "miniature",
        "Miniature",
        "tabletop miniature interpretation, readable silhouette, reinforced thin features, sculpted details suitable for small-scale printing",
        "text, logos, disconnected parts, paper-thin surfaces",
    ),
    "bobblehead": StylePreset(
        "bobblehead",
        "Bobblehead",
        "bobblehead collectible figure, oversized head, compact stylized body, simplified facial likeness, sturdy neck connection, display-ready pose",
        "text, logos, fragile neck, floating parts",
    ),
    "realistic-bust": StylePreset(
        "realistic-bust",
        "Realistic Bust",
        "realistic sculpted bust, recognizable facial identity, simplified printable hair masses, shoulders and upper torso, neutral presentation",
        "text, logos, loose hair strands, floating geometry",
    ),
    "low-poly": StylePreset(
        "low-poly",
        "Low Poly",
        "low-poly stylized figure, faceted surfaces, strong silhouette, simplified topology, preserve recognizable subject characteristics",
        "text, logos, noisy microdetail, floating geometry",
    ),
}


class UnknownStylePresetError(ValueError):
    pass


class StylePreprocessingError(RuntimeError):
    pass


class StylePreprocessor(Protocol):
    def stylize(self, source: StoredImageAsset, preset: StylePreset) -> StoredImageAsset: ...


class PassThroughStylePreprocessor:
    """Deterministic CI/local fallback that preserves the processed image unchanged."""

    def stylize(self, source: StoredImageAsset, preset: StylePreset) -> StoredImageAsset:
        return source


class RunnerStylePreprocessor:
    """External image stylization adapter isolated from the ARTIFEX API process."""

    def __init__(
        self,
        store: FileAssetStore | None = None,
        command: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._store = store or FileAssetStore()
        self._command = command or os.getenv("ARTIFEX_STYLE_COMMAND")
        configured_timeout = os.getenv("ARTIFEX_STYLE_TIMEOUT_SECONDS")
        self._timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else float(configured_timeout or "900")
        )

    def stylize(self, source: StoredImageAsset, preset: StylePreset) -> StoredImageAsset:
        if preset.style_id == "none":
            return source
        if not self._command:
            raise StylePreprocessingError(
                "Style generation is not configured. Set ARTIFEX_STYLE_COMMAND or use style=none."
            )

        with tempfile.TemporaryDirectory(prefix="artifex-style-") as temp_dir:
            work_dir = Path(temp_dir)
            output_dir = work_dir / "output"
            output_dir.mkdir()
            request_path = work_dir / "request.json"
            request_path.write_text(
                json.dumps(
                    {
                        "inputPath": str(source.path.resolve()),
                        "outputDirectory": str(output_dir.resolve()),
                        "styleId": preset.style_id,
                        "prompt": preset.prompt,
                        "negativePrompt": preset.negative_prompt,
                        "preserveIdentity": True,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            try:
                completed = subprocess.run(
                    [*shlex.split(self._command), "--request", str(request_path)],
                    capture_output=True,
                    text=True,
                    timeout=self._timeout_seconds,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise StylePreprocessingError("Style runner could not complete") from exc

            if completed.returncode != 0:
                raise StylePreprocessingError(completed.stderr.strip() or "Style runner failed")

            manifest_path = output_dir / "result.json"
            if not manifest_path.is_file():
                raise StylePreprocessingError("Style runner did not produce result.json")
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                relative_path = str(manifest["image"]["path"])
                media_type = str(manifest["image"].get("mediaType", "image/png"))
                image_path = (output_dir / relative_path).resolve()
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise StylePreprocessingError("Style runner result is invalid") from exc

            if output_dir.resolve() not in image_path.parents or not image_path.is_file():
                raise StylePreprocessingError("Style runner returned an invalid output path")
            suffix = image_path.suffix or ".png"
            return self._store.save(image_path.read_bytes(), media_type, suffix)


def resolve_style_preset(style_id: str) -> StylePreset:
    preset = STYLE_PRESETS.get(style_id)
    if preset is None:
        raise UnknownStylePresetError(style_id)
    return preset
