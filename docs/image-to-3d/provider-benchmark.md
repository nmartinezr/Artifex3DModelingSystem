# Image → 3D Provider Benchmark

This document defines the ARTIFEX benchmark contract for selecting Image → 3D inference engines. Provider output is always treated as raw generated geometry, not as automatically printable geometry.

## Candidate providers

| Provider | ARTIFEX ID | Current role | Notes |
| --- | --- | --- | --- |
| Fixture | `fixture` | CI/local smoke-test baseline | Deterministic cube; no inference |
| TRELLIS | `trellis` | Primary high-quality candidate | Flexible mesh/3D representation pipeline; runner already integrated |
| SPAR3D | `spar3d` | Primary reconstruction candidate | Point-aware conditioning explicitly targets improved backside reconstruction |
| Stable Fast 3D | `stable-fast-3d` | Fast/lower-resource fallback candidate | Fast single-image reconstruction; official repo documents ~6 GB VRAM for default inference |
| Hunyuan3D | `hunyuan3d` | Experimental candidate | Adapter available; licensing/commercial constraints require explicit review before production default |

## Runner boundary

All real providers are isolated from the ARTIFEX API process. A configured command receives:

```text
<runner command> --request <request.json>
```

The request points to the preprocessed image and an output directory. The runner must produce `result.json` plus referenced output assets using ARTIFEX conventions:

```json
{
  "conventions": {
    "unit": "mm",
    "handedness": "right",
    "upAxis": "Z"
  },
  "mesh": {
    "path": "model.glb",
    "mediaType": "model/gltf-binary",
    "triangleCount": 0,
    "vertexCount": 0,
    "boundsMm": {
      "min": [0, 0, 0],
      "max": [0, 0, 0]
    }
  },
  "textures": []
}
```

This keeps CUDA/PyTorch/model-specific dependencies outside the application and allows providers to be replaced without changing validation, viewer, project-model or export code.

ARTIFEX also includes `tools/image_to_3d/generic_cli_runner.py`. It adapts CLI-based engines that accept an input image and produce a GLB, normalizes the model to a configurable physical size, extracts mesh metrics and emits the common runner manifest. Provider-specific runners remain appropriate when an engine needs richer texture/material handling or non-standard inference orchestration.

## Configuration

| Provider | Environment variable |
| --- | --- |
| TRELLIS | `ARTIFEX_TRELLIS_COMMAND` |
| SPAR3D | `ARTIFEX_SPAR3D_COMMAND` |
| Stable Fast 3D | `ARTIFEX_STABLE_FAST_3D_COMMAND` |
| Hunyuan3D | `ARTIFEX_HUNYUAN3D_COMMAND` |

## Benchmark dataset

Use the canonical procedural dataset under `tests/regression/image_to_3d/` for every provider. Cases cover product-like objects, figurines, animals, asymmetry, thin features, difficult silhouettes/backgrounds and transparency.

GPU-heavy runs are intentionally kept out of normal CI. Each real-provider benchmark should use the same source cases and record the exact provider/model/version and hardware.

## Required metrics

For every case/provider capture:

- generation success/failure and stable error code;
- generation duration;
- peak VRAM where the runner can expose it;
- vertex and triangle counts;
- disconnected component count;
- watertightness;
- boundary and non-manifold edge counts;
- degenerate faces;
- dimensions/bounds;
- texture availability;
- visual reconstruction observations, including backside/occluded geometry;
- repairability/expected manufacturing cleanup;
- provider/model/license version.

## Initial recommendation

The architecture should keep multiple providers available rather than selecting a permanent single engine.

For the next real-GPU comparison:

1. **TRELLIS** remains the high-quality reference candidate.
2. **SPAR3D** is the strongest next integration target because its design specifically addresses backside reconstruction, which matters for a manufacturing workflow.
3. **Stable Fast 3D** is the lower-resource fallback and useful performance baseline.
4. **Hunyuan3D** remains experimental until its production/commercial licensing position is explicitly accepted for ARTIFEX.

A final default-provider decision must be based on actual runs of the canonical dataset on comparable hardware; no quality or performance numbers should be fabricated when a model has not been executed.

## Current implementation status

The provider-selection architecture is implemented for all four real candidates. TRELLIS has its existing runner path, while SPAR3D, Stable Fast 3D and Hunyuan3D share the normalized runner contract and can be wired to provider-specific runners or the generic CLI adapter.

This completes the interchangeable-provider application architecture but **does not complete the empirical benchmark acceptance criteria**. Issue #12 remains open until the canonical dataset is actually executed across viable real providers on comparable GPU hardware and the measured results are recorded.

## Manufacturing principle

A visually convincing result can still contain open boundaries, non-manifold regions, floating components, incorrect scale or topology unsuitable for printing. Provider ranking therefore considers both visual reconstruction and the amount of deterministic repair needed before manufacturing.
