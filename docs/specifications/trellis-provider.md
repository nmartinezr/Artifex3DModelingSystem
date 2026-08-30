# TRELLIS provider integration

## Status
Initial Image → 3D provider for ARTIFEX M1.

## Isolation model
ARTIFEX does **not** import TRELLIS, PyTorch, CUDA, model weights or renderer dependencies into `apps/api`.

`TrellisProvider` launches a separately configured runner using:

```text
ARTIFEX API
  -> ImageTo3DProvider
  -> TrellisProvider
  -> ARTIFEX_TRELLIS_COMMAND --request <request.json>
  -> TRELLIS runtime/GPU environment
```

This is intentional. The provider runtime can be replaced, containerized, upgraded to TRELLIS.2, or moved to another machine without changing application contracts.

## Runtime configuration
Set:

```bash
ARTIFEX_TRELLIS_COMMAND="python /path/to/artifex_trellis_runner.py"
```

The runner environment owns installation of CUDA/PyTorch and the TRELLIS repository/model weights. The API process does not install those dependencies.

Default model identifier:

```text
microsoft/TRELLIS-image-large
```

The adapter accepts configurable model, model version, timeout, seed, quality, texture generation flag and provider-specific options.

## Runner request
The configured command receives:

```text
--request /absolute/path/request.json
```

Request JSON contains:

```json
{
  "inputPath": "/absolute/path/input.png",
  "outputDirectory": "/absolute/path/output",
  "model": "microsoft/TRELLIS-image-large",
  "modelVersion": null,
  "seed": 7,
  "quality": "balanced",
  "generateTexture": true,
  "providerOptions": {},
  "outputConventions": {
    "unit": "mm",
    "handedness": "right",
    "upAxis": "Z"
  }
}
```

## Runner result
The runner must create `result.json` under `outputDirectory` and all referenced assets must remain inside that directory.

```json
{
  "name": "Generated model",
  "conventions": {
    "unit": "mm",
    "handedness": "right",
    "upAxis": "Z"
  },
  "mesh": {
    "path": "model.glb",
    "mediaType": "model/gltf-binary",
    "triangleCount": 12345,
    "vertexCount": 6200,
    "boundsMm": {
      "min": [-25.0, -20.0, 0.0],
      "max": [25.0, 20.0, 80.0]
    }
  },
  "textures": [
    {"path": "albedo.png", "mediaType": "image/png"}
  ]
}
```

ARTIFEX rejects results that are not explicitly normalized to canonical `mm`, right-handed, Z-up conventions. This prevents provider-specific scale/orientation assumptions from silently entering the Project Model.

## Persistence
The adapter copies provider outputs into the ARTIFEX asset store, generating ARTIFEX-owned asset IDs and checksums. Temporary runner output is deleted after ingestion.

The generation result also includes a canonical Project Model `sceneObject` fragment with identity transform, mesh metrics, bounds and provider provenance.

## Error mapping

| Provider/runner condition | ARTIFEX code |
| --- | --- |
| Runner not configured/cannot start | `IMAGE_TO_3D_PROVIDER_UNAVAILABLE` |
| Input asset missing | `IMAGE_TO_3D_INVALID_INPUT` |
| Timeout | `IMAGE_TO_3D_TIMEOUT` |
| CUDA/GPU OOM or exit 137 | `IMAGE_TO_3D_RESOURCE_EXHAUSTED` |
| Missing/malformed result or wrong conventions | `IMAGE_TO_3D_INVALID_OUTPUT` |
| Other runner failure | `IMAGE_TO_3D_GENERATION_FAILED` |

## Licensing boundary
TRELLIS models and most of the original TRELLIS code are published under MIT, while some submodules/dependencies use separate licenses. The sidecar boundary keeps those dependencies out of the ARTIFEX application package and requires the deployed runner image/environment to maintain its own dependency/license inventory.

Before commercial deployment, re-check the exact TRELLIS/TRELLIS.2 revision and every runtime dependency used by the chosen runner image.

## CI strategy
Normal CI uses deterministic fake runners and the existing mock provider. Real TRELLIS execution belongs in a separate GPU integration suite and must not block routine frontend/backend CI.
