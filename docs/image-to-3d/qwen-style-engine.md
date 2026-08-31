# Qwen Image Edit style engine

ARTIFEX can use Qwen Image Edit as the first real implementation behind `StylePreprocessor`.

## Why Qwen Image Edit

Qwen Image Edit is an instruction-driven image editing model suited to preserving subject identity while changing visual style. ARTIFEX keeps it outside the API process so model dependencies, GPU requirements and future model replacements remain isolated from the application architecture.

The default ARTIFEX runner model is:

```text
Qwen/Qwen-Image-Edit-2509
```

## Pipeline

```text
Uploaded image
  → ARTIFEX preprocessing/background removal
  → selected style preset
  → Qwen Image Edit runner
  → styled PNG
  → selected ImageTo3DProvider
  → geometry validation
  → GLB / STL / 3MF
```

## Install a dedicated style environment

Using a separate virtual environment is recommended because PyTorch and model dependencies are intentionally not dependencies of the ARTIFEX API.

Windows PowerShell example:

```powershell
python -m venv .venv-style
.\.venv-style\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install a PyTorch build appropriate for the machine/GPU first, then install the model stack:

```powershell
pip install -U diffusers transformers accelerate safetensors pillow sentencepiece
```

For CUDA systems, install the PyTorch CUDA build recommended for the installed NVIDIA driver before the command above.

## Configure ARTIFEX

Start ARTIFEX from the repository root and point `ARTIFEX_STYLE_COMMAND` at the Python executable from the style environment.

Example when the style environment is activated:

```powershell
$env:ARTIFEX_STYLE_COMMAND = "python tools/image_to_3d/qwen_image_edit_style_runner.py"
$env:ARTIFEX_STYLE_TIMEOUT_SECONDS = "900"
```

For systems with limited VRAM, enable model CPU offload:

```powershell
$env:ARTIFEX_QWEN_IMAGE_EDIT_CPU_OFFLOAD = "1"
```

Optional deterministic/tuning settings:

```powershell
$env:ARTIFEX_QWEN_IMAGE_EDIT_MODEL = "Qwen/Qwen-Image-Edit-2509"
$env:ARTIFEX_QWEN_IMAGE_EDIT_STEPS = "30"
$env:ARTIFEX_QWEN_IMAGE_EDIT_GUIDANCE_SCALE = "4.0"
$env:ARTIFEX_QWEN_IMAGE_EDIT_SEED = "42"
```

Then start the API normally:

```powershell
uvicorn artifex_api.main:app --reload --app-dir apps/api/src
```

The first real inference downloads model weights through the Hugging Face stack unless they are already cached. Model inference can be memory intensive; CPU offload reduces VRAM pressure but increases latency and system-RAM usage.

## First ARTIFEX experiment

Use:

```text
Style: Collectible Vinyl
Provider: a configured real Image→3D provider
```

The style engine creates a brand-neutral collectible-vinyl interpretation using the preset prompt. It is intentionally not branded as or designed to reproduce Funko products, logos or packaging.

For initial validation, the style engine may also be combined with `Provider: Fixture`. In that configuration the Qwen stylization stage is real, but the final 3D output remains the deterministic cube. This is useful for isolating and validating the image-style stage before introducing GPU-heavy 3D generation.

## Runner contract

The API invokes:

```text
python tools/image_to_3d/qwen_image_edit_style_runner.py --request <request.json>
```

The request contains source path, output directory, style ID, prompt, negative prompt and identity-preservation intent. The runner writes:

```text
output/
  styled.png
  result.json
```

`result.json` contains the styled-image path plus model/seed/inference provenance.

## Operational notes

- Keep the style environment separate from the ARTIFEX API environment.
- Keep `style=none` as the deterministic no-model path for CI.
- Do not silently fall back from a requested style to the original image.
- Use a fixed seed for reproducible QA comparisons.
- Benchmark identity preservation and print-oriented silhouette quality before changing the default style model.
- Qwen is the first adapter, not a permanent architectural dependency; FLUX Kontext and other editing models can be integrated behind the same contract later.
