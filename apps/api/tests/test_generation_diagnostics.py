from __future__ import annotations

from artifex_api.image_to_3d.diagnostics import GenerationTelemetryRecord, sanitized_parameters


def test_sanitized_parameters_excludes_sensitive_or_payload_fields() -> None:
    result = sanitized_parameters(
        {
            "quality": "balanced",
            "seed": 42,
            "apiKey": "secret",
            "token": "secret",
            "sourceImage": b"raw-bytes",
            "inputPath": "/tmp/private.png",
            "nested": {"arbitrary": "payload"},
        }
    )

    assert result == {"quality": "balanced", "seed": 42}


def test_telemetry_record_contains_analysis_fields_without_raw_image_content() -> None:
    record = GenerationTelemetryRecord(
        correlation_id="gen_test",
        provider="fixture",
        model="deterministic-cube",
        model_version="1",
        parameters={"quality": "balanced"},
        input_width=64,
        input_height=64,
        preprocessing_duration_ms=1.0,
        generation_duration_ms=2.0,
        validation_duration_ms=3.0,
        total_duration_ms=6.0,
        vertex_count=8,
        triangle_count=12,
        component_count=1,
        validation_summary={"score": 100, "exportBlocked": False},
    )

    payload = record.to_dict()
    assert payload["correlation_id"] == "gen_test"
    assert payload["triangle_count"] == 12
    assert "image" not in " ".join(payload.keys()).lower()
