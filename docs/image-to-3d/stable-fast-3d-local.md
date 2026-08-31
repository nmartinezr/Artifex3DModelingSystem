# Stable Fast 3D local runtime

This guide enables the first ARTIFEX local path that displays a real reconstructed mesh instead of the deterministic fixture cube.

## Resulting flow

```text
Source image
  → ARTIFEX preprocessing
  → optional Qwen style preprocessing
  → Stable Fast 3D
  → normalized GLB
  → ARTIFEX geometry validation
  → Three.js viewer
  → GLB / STL / 3MF export
```

## Requirements

Stable Fast 3D is maintained by Stability AI at `Stability-AI/stable-fast-3d`.

The upstream project currently documents:

- Python 3.8+
- CUDA is recommended; CPU fallback is supported
- Windows support is experimental and requires Visual Studio 2022 for native build dependencies
- default single-image inference uses about 6 GB of VRAM
- the model is gated on Hugging Face and requires accepting access plus authenticating with a read token

Keep Stable Fast 3D in its own Python environment. Do not install its pinned ML dependencies into the ARTIFEX API virtual environment.

## 1. Clone Stable Fast 3D

From the ARTIFEX repository root:

```powershell
New-Item -ItemType Directory -Force external | Out-Null
git clone https://github.com/Stability-AI/stable-fast-3d.git external/stable-fast-3d
```

## 2. Create an isolated SF3D environment

```powershell
py -3.11 -m venv .venv-sf3d
.\.venv-sf3d\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -U setuptools==69.5.1 wheel
```

Install PyTorch for your CUDA/CPU platform following the official PyTorch selector, then install Stable Fast 3D requirements:

```powershell
pip install -r external/stable-fast-3d/requirements.txt
```

## 3. Request/authenticate Hugging Face access

Request access to `stabilityai/stable-fast-3d` on Hugging Face, create a read token, then authenticate in the SF3D environment:

```powershell
huggingface-cli login
```

The first inference downloads the model weights into the Hugging Face cache.

## 4. Configure ARTIFEX

Open the terminal that will run the ARTIFEX API and activate the normal ARTIFEX environment, not `.venv-sf3d`:

```powershell
.\.venv\Scripts\Activate.ps1
```

Configure the bundled ARTIFEX runner and point it to the isolated SF3D Python executable:

```powershell
$env:ARTIFEX_STABLE_FAST_3D_COMMAND = "python tools/image_to_3d/stable_fast_3d_runner.py"
$env:ARTIFEX_SF3D_REPO = "$PWD\external\stable-fast-3d"
$env:ARTIFEX_SF3D_PYTHON = "$PWD\.venv-sf3d\Scripts\python.exe"
$env:ARTIFEX_STABLE_FAST_3D_TIMEOUT_SECONDS = "900"
```

Optional tuning:

```powershell
$env:ARTIFEX_SF3D_TEXTURE_RESOLUTION = "1024"
$env:ARTIFEX_SF3D_REMESH_OPTION = "none"
$env:ARTIFEX_SF3D_TARGET_SIZE_MM = "100"
```

If you explicitly need CPU execution, set the upstream switch before starting the API:

```powershell
$env:SF3D_USE_CPU = "1"
```

## 5. Start ARTIFEX

API:

```powershell
uvicorn artifex_api.main:app --reload --app-dir apps/api/src
```

Web app in a second terminal:

```powershell
cd apps/web
npm run dev
```

## 6. First real 3D test

For the simplest test that removes the cube without adding Qwen cost yet:

```text
Style: Original
Provider: Stable Fast 3D
```

Upload a PNG/JPEG/WebP containing one clear subject. ARTIFEX preprocesses the image, invokes the bundled Stable Fast 3D runner, stores the normalized GLB, validates it and sends that GLB to the existing Three.js viewer.

If generation succeeds, the viewer is displaying the Stable Fast 3D mesh, not the fixture cube.

## 7. Full style + real 3D test

After the Qwen style environment is configured, select for example:

```text
Style: Collectible Vinyl
Provider: Stable Fast 3D
```

The conditioning image sent to Stable Fast 3D will be the Qwen-stylized image rather than the original upload.

## Diagnostics

### `Stable Fast 3D runner is not configured`

`ARTIFEX_STABLE_FAST_3D_COMMAND` was not set in the API process.

### `Stable Fast 3D is not installed`

`ARTIFEX_SF3D_REPO` does not point to an upstream checkout containing `run.py`.

### Hugging Face authorization/download error

Confirm access to `stabilityai/stable-fast-3d` and authenticate from the `.venv-sf3d` environment.

### CUDA out of memory

Try a lower texture resolution or CPU execution. The upstream default path is documented at roughly 6 GB VRAM for one image, but practical usage varies by platform and driver/runtime overhead.

### Timeout

Increase:

```powershell
$env:ARTIFEX_STABLE_FAST_3D_TIMEOUT_SECONDS = "1800"
```

CPU generation can require substantially more time than CUDA execution.
