from __future__ import annotations

import pytest

from artifex_api.image_to_3d.preprocessing import FileAssetStore
from artifex_api.image_to_3d.style_preprocessing import (
    STYLE_PRESETS,
    RunnerStylePreprocessor,
    StylePreprocessingError,
    UnknownStylePresetError,
    resolve_style_preset,
)


def test_collectible_vinyl_preset_is_brand_neutral_and_print_oriented() -> None:
    preset = resolve_style_preset("collectible-vinyl")

    assert preset.display_name == "Collectible Vinyl"
    assert "oversized head" in preset.prompt
    assert "printable" in preset.prompt
    assert "funko" not in preset.prompt.lower()
    assert "brand logos" in preset.negative_prompt


def test_style_catalog_has_expected_initial_presets() -> None:
    assert {
        "none",
        "collectible-vinyl",
        "chibi",
        "anime-figure",
        "cartoon",
        "miniature",
        "bobblehead",
        "realistic-bust",
        "low-poly",
    }.issubset(STYLE_PRESETS)


def test_unknown_style_is_rejected() -> None:
    with pytest.raises(UnknownStylePresetError):
        resolve_style_preset("does-not-exist")


def test_none_style_does_not_require_external_runner(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARTIFEX_STYLE_COMMAND", raising=False)
    store = FileAssetStore(tmp_path)
    source = store.save(b"image", "image/png", ".png")
    processor = RunnerStylePreprocessor(store=store)

    assert processor.stylize(source, resolve_style_preset("none")) == source


def test_stylized_preset_requires_configured_runner(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARTIFEX_STYLE_COMMAND", raising=False)
    store = FileAssetStore(tmp_path)
    source = store.save(b"image", "image/png", ".png")
    processor = RunnerStylePreprocessor(store=store)

    with pytest.raises(StylePreprocessingError, match="ARTIFEX_STYLE_COMMAND"):
        processor.stylize(source, resolve_style_preset("collectible-vinyl"))


def test_style_runner_timeout_can_be_configured(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ARTIFEX_STYLE_TIMEOUT_SECONDS", "1234")
    processor = RunnerStylePreprocessor(store=FileAssetStore(tmp_path), command="fake-runner")

    assert processor._timeout_seconds == 1234.0
