[CmdletBinding()]
param(
    [string]$PythonVersion = "3.11",
    [string]$TorchIndexUrl = "",
    [switch]$ForceCpu,
    [switch]$SkipRequirements
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$externalDir = Join-Path $repoRoot "external"
$sf3dRepo = Join-Path $externalDir "stable-fast-3d"
$venvDir = Join-Path $repoRoot ".venv-sf3d"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$hfCli = Join-Path $venvDir "Scripts\huggingface-cli.exe"
$envDir = Join-Path $repoRoot ".artifex"
$envScript = Join-Path $envDir "sf3d-env.ps1"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Assert-Command([string]$Name, [string]$InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found. $InstallHint"
    }
}

Write-Step "Checking required tools"
Assert-Command "git" "Install Git for Windows and reopen PowerShell."
Assert-Command "py" "Install Python $PythonVersion from python.org with the Windows py launcher enabled."

$vsWhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vsWhere)) {
    Write-Warning "Visual Studio 2022 was not detected. Stable Fast 3D Windows support is experimental and native dependencies may fail to build. Install Visual Studio 2022 Build Tools with Desktop development with C++."
} else {
    $vsInstall = & $vsWhere -latest -products * -version "[17.0,18.0)" -property installationPath
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($vsInstall)) {
        Write-Warning "Visual Studio 2022 installation was not detected by vswhere. Native dependency builds may fail."
    } else {
        Write-Host "Visual Studio 2022: $vsInstall"
    }
}

$nvidia = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
if ($ForceCpu) {
    Write-Host "Runtime mode: CPU (forced)"
} elseif ($nvidia) {
    Write-Host "Runtime mode: NVIDIA GPU detected"
    & nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
} else {
    Write-Warning "No NVIDIA GPU was detected. Stable Fast 3D will use CPU unless another supported backend is available."
}

Write-Step "Preparing upstream Stable Fast 3D repository"
New-Item -ItemType Directory -Force $externalDir | Out-Null
if (-not (Test-Path (Join-Path $sf3dRepo "run.py"))) {
    if (Test-Path $sf3dRepo) {
        throw "$sf3dRepo exists but does not contain run.py. Remove or repair that directory before retrying."
    }
    & git clone https://github.com/Stability-AI/stable-fast-3d.git $sf3dRepo
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to clone Stability-AI/stable-fast-3d."
    }
} else {
    Write-Host "Stable Fast 3D repository already present: $sf3dRepo"
}

Write-Step "Creating isolated Python environment"
if (-not (Test-Path $pythonExe)) {
    & py "-$PythonVersion" -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to create .venv-sf3d with Python $PythonVersion. Verify it is installed with: py -0p"
    }
}

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install "setuptools==69.5.1" wheel

Write-Step "Checking PyTorch"
$torchAvailable = $true
& $pythonExe -c "import torch; print('torch=' + torch.__version__ + ', cuda=' + str(torch.cuda.is_available()))" 2>$null
if ($LASTEXITCODE -ne 0) {
    $torchAvailable = $false
}

if (-not $torchAvailable) {
    if ($ForceCpu) {
        Write-Host "Installing CPU PyTorch wheels"
        & $pythonExe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
        if ($LASTEXITCODE -ne 0) {
            throw "CPU PyTorch installation failed."
        }
    } elseif (-not [string]::IsNullOrWhiteSpace($TorchIndexUrl)) {
        Write-Host "Installing PyTorch from explicit index: $TorchIndexUrl"
        & $pythonExe -m pip install torch torchvision --index-url $TorchIndexUrl
        if ($LASTEXITCODE -ne 0) {
            throw "PyTorch installation failed for index $TorchIndexUrl."
        }
    } else {
        throw @"
PyTorch is not installed in .venv-sf3d. ARTIFEX will not guess a CUDA wheel because it must match your system.
Install PyTorch for your platform, then rerun this script. Example:
  .\.venv-sf3d\Scripts\python.exe -m pip install torch torchvision --index-url <PYTORCH_INDEX_URL>
Or rerun with:
  .\scripts\setup-stable-fast-3d.ps1 -TorchIndexUrl <PYTORCH_INDEX_URL>
For CPU only:
  .\scripts\setup-stable-fast-3d.ps1 -ForceCpu
Choose the correct command at https://pytorch.org/get-started/locally/
"@
    }
}

if (-not $SkipRequirements) {
    Write-Step "Installing Stable Fast 3D dependencies"
    Push-Location $sf3dRepo
    try {
        & $pythonExe -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Stable Fast 3D requirements installation failed. On Windows, verify Visual Studio 2022 C++ build tools and that your PyTorch/CUDA combination is compatible."
        }
    } finally {
        Pop-Location
    }
}

Write-Step "Generating ARTIFEX runtime environment"
New-Item -ItemType Directory -Force $envDir | Out-Null
$escapedRepoRoot = $repoRoot.Replace("'", "''")
$escapedSf3dRepo = $sf3dRepo.Replace("'", "''")
$escapedPython = $pythonExe.Replace("'", "''")
$cpuLine = if ($ForceCpu) { '$env:SF3D_USE_CPU = "1"' } else { '# $env:SF3D_USE_CPU = "1"  # Uncomment to force CPU mode.' }
@"
# Generated by scripts/setup-stable-fast-3d.ps1
`$env:ARTIFEX_STABLE_FAST_3D_COMMAND = "python tools/image_to_3d/stable_fast_3d_runner.py"
`$env:ARTIFEX_SF3D_REPO = '$escapedSf3dRepo'
`$env:ARTIFEX_SF3D_PYTHON = '$escapedPython'
`$env:ARTIFEX_STABLE_FAST_3D_TIMEOUT_SECONDS = "900"
`$env:ARTIFEX_SF3D_TEXTURE_RESOLUTION = "1024"
`$env:ARTIFEX_SF3D_REMESH_OPTION = "none"
`$env:ARTIFEX_SF3D_TARGET_SIZE_MM = "100"
$cpuLine
Set-Location '$escapedRepoRoot'
"@ | Set-Content -Path $envScript -Encoding UTF8

Write-Step "Checking Hugging Face authentication"
if (Test-Path $hfCli) {
    & $hfCli whoami 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Hugging Face is not authenticated. Request access to stabilityai/stable-fast-3d, then run: .\.venv-sf3d\Scripts\huggingface-cli.exe login"
    }
} else {
    Write-Warning "huggingface-cli was not found in .venv-sf3d. Complete dependency installation before authenticating."
}

Write-Host "`nStable Fast 3D bootstrap completed." -ForegroundColor Green
Write-Host "Load ARTIFEX variables with:"
Write-Host "  . .\.artifex\sf3d-env.ps1" -ForegroundColor Yellow
Write-Host "Then validate with:"
Write-Host "  .\scripts\check-stable-fast-3d.ps1" -ForegroundColor Yellow
