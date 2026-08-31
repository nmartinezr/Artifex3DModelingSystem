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

## Recommended Windows bootstrap

From the ARTIFEX repository root, first update `develop`:

```powershell
git switch develop
git pull origin develop
```

Then run the ARTIFEX bootstrap:

```powershell
.\scripts\setup-stable-fast-3d.ps1
```

The bootstrap:

- verifies Git and Python 3.11
- detects Visual Studio 2022 when available
- reports the detected NVIDIA GPU/driver
- clones `Stability-AI/stable-fast-3d` into `external/stable-fast-3d`
- creates `.venv-sf3d`
- installs the exact upstream setup prerequisites
- validates PyTorch before installing model dependencies
- installs Stable Fast 3D requirements
- creates `.artifex\sf3d-env.ps1` with ARTIFEX runtime variables
- reports whether Hugging Face authentication is active

### PyTorch on NVIDIA GPUs

ARTIFEX deliberately does **not** guess a CUDA PyTorch wheel. PyTorch must match the machine's supported CUDA/runtime combination.

If PyTorch is not already present, the bootstrap stops before the heavy Stable Fast 3D dependency installation and gives an actionable message. Use the official PyTorch selector, then either install PyTorch directly into `.venv-sf3d` or rerun with the selected wheel index:

```powershell
.\scripts\setup-stable-fast-3d.ps1 -TorchIndexUrl <PYTORCH_INDEX_URL>
```

Example shape only; use the value returned by the official PyTorch selector for the current machine:

```powershell
.\scripts\setup-stable-fast-3d.ps1 -TorchIndexUrl https://download.pytorch.org/whl/cuXXX
```

Do not copy `cuXXX` literally.

### CPU-only setup

For a deterministic CPU installation:

```powershell
.\scripts\setup-stable-fast-3d.ps1 -ForceCpu
```

This installs CPU PyTorch wheels and writes `SF3D_USE_CPU=1` into the generated ARTIFEX environment script. CPU inference is expected to be much slower.

## Validate the runtime

After setup:

```powershell
.\scripts\check-stable-fast-3d.ps1
```

Expected checks include:

```text
[PASS] Upstream Stable Fast 3D repository detected.
[PASS] Python environment detected: Python 3.11.x
[PASS] PyTorch ... available (CUDA: ...).
[PASS] Core Stable Fast 3D Python dependencies are importable.
[PASS] ARTIFEX environment script detected: .artifex\sf3d-env.ps1
```

Hugging Face authentication can still appear as a warning until model access is configured.

## Hugging Face access

The model is gated. Request access to `stabilityai/stable-fast-3d` on Hugging Face, create a read token, then authenticate using the isolated runtime:

```powershell
.\.venv-sf3d\Scripts\huggingface-cli.exe login
```

Run the health check again afterward:

```powershell
.\scripts\check-stable-fast-3d.ps1
```

The first real inference downloads the model weights into the Hugging Face cache.

## Load the ARTIFEX runtime configuration

The bootstrap generates `.artifex\sf3d-env.ps1`. Dot-source it in the PowerShell terminal that will run the ARTIFEX API:

```powershell
. .\.artifex\sf3d-env.ps1
```

This configures:

```text
ARTIFEX_STABLE_FAST_3D_COMMAND
ARTIFEX_SF3D_REPO
ARTIFEX_SF3D_PYTHON
ARTIFEX_STABLE_FAST_3D_TIMEOUT_SECONDS
ARTIFEX_SF3D_TEXTURE_RESOLUTION
ARTIFEX_SF3D_REMESH_OPTION
ARTIFEX_SF3D_TARGET_SIZE_MM
```

The generated `.artifex/`, `.venv-sf3d/` and upstream checkout are local-only and ignored by Git.

## Start ARTIFEX

Activate the normal ARTIFEX API environment in the same terminal after loading the SF3D variables:

```powershell
.\.venv\Scripts\Activate.ps1
. .\.artifex\sf3d-env.ps1
uvicorn artifex_api.main:app --reload --app-dir apps/api/src
```

Start the web app in a second terminal:

```powershell
cd apps/web
npm install
npm run dev
```

## First real 3D test

For the simplest test that removes the cube without adding Qwen cost yet:

```text
Style: Original
Provider: Stable Fast 3D
```

Upload a PNG/JPEG/WebP containing one clear subject. ARTIFEX preprocesses the image, invokes the bundled Stable Fast 3D runner, stores the normalized GLB, validates it and sends that GLB to the existing Three.js viewer.

If generation succeeds, the viewer is displaying the Stable Fast 3D mesh, not the fixture cube.

## Full style + real 3D test

After the Qwen style environment is configured, select for example:

```text
Style: Collectible Vinyl
Provider: Stable Fast 3D
```

The conditioning image sent to Stable Fast 3D will be the Qwen-stylized image rather than the original upload.

## Manual setup fallback

If the bootstrap cannot be used, the equivalent manual setup is:

```powershell
New-Item -ItemType Directory -Force external | Out-Null
git clone https://github.com/Stability-AI/stable-fast-3d.git external/stable-fast-3d
py -3.11 -m venv .venv-sf3d
.\.venv-sf3d\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -U setuptools==69.5.1 wheel
```

Install PyTorch for the platform using the official PyTorch selector, then:

```powershell
pip install -r external/stable-fast-3d/requirements.txt
huggingface-cli login
```

Configure ARTIFEX:

```powershell
$env:ARTIFEX_STABLE_FAST_3D_COMMAND = "python tools/image_to_3d/stable_fast_3d_runner.py"
$env:ARTIFEX_SF3D_REPO = "$PWD\external\stable-fast-3d"
$env:ARTIFEX_SF3D_PYTHON = "$PWD\.venv-sf3d\Scripts\python.exe"
$env:ARTIFEX_STABLE_FAST_3D_TIMEOUT_SECONDS = "900"
$env:ARTIFEX_SF3D_TEXTURE_RESOLUTION = "1024"
$env:ARTIFEX_SF3D_REMESH_OPTION = "none"
$env:ARTIFEX_SF3D_TARGET_SIZE_MM = "100"
```

## Diagnostics

### `Stable Fast 3D runner is not configured`

`ARTIFEX_STABLE_FAST_3D_COMMAND` was not set in the API process. Load `.artifex\sf3d-env.ps1` before starting the API.

### `Stable Fast 3D is not installed`

`ARTIFEX_SF3D_REPO` does not point to an upstream checkout containing `run.py`.

### Hugging Face authorization/download error

Confirm access to `stabilityai/stable-fast-3d` and authenticate from `.venv-sf3d`.

### Native wheel/compiler failure on Windows

Verify Visual Studio 2022 Build Tools with the C++ workload and ensure the selected PyTorch/CUDA combination is compatible. Upstream Windows support remains experimental.

### CUDA out of memory

Try a lower texture resolution or CPU execution. The upstream default path is documented at roughly 6 GB VRAM for one image, but practical usage varies by platform and driver/runtime overhead.

### Timeout

Increase:

```powershell
$env:ARTIFEX_STABLE_FAST_3D_TIMEOUT_SECONDS = "1800"
```

CPU generation can require substantially more time than CUDA execution.
