[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$sf3dRepo = Join-Path $repoRoot "external\stable-fast-3d"
$pythonExe = Join-Path $repoRoot ".venv-sf3d\Scripts\python.exe"
$hfCli = Join-Path $repoRoot ".venv-sf3d\Scripts\huggingface-cli.exe"
$envScript = Join-Path $repoRoot ".artifex\sf3d-env.ps1"
$failed = $false

function Pass([string]$Message) {
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Warn([string]$Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Fail([string]$Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    $script:failed = $true
}

Write-Host "ARTIFEX Stable Fast 3D runtime check`n" -ForegroundColor Cyan

if (Test-Path (Join-Path $sf3dRepo "run.py")) {
    Pass "Upstream Stable Fast 3D repository detected."
} else {
    Fail "Stable Fast 3D repository missing at $sf3dRepo. Run .\scripts\setup-stable-fast-3d.ps1"
}

if (Test-Path $pythonExe) {
    $version = & $pythonExe --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Pass "Python environment detected: $version"
    } else {
        Fail ".venv-sf3d Python executable could not start."
    }
} else {
    Fail ".venv-sf3d is missing. Run .\scripts\setup-stable-fast-3d.ps1"
}

if (Test-Path $pythonExe) {
    $torchInfo = & $pythonExe -c "import torch; print(f'{torch.__version__}|{torch.cuda.is_available()}|{torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $parts = $torchInfo -split '\|'
        $backend = if ($parts[1] -eq "True") { "CUDA: $($parts[2])" } else { "CPU" }
        Pass "PyTorch $($parts[0]) available ($backend)."
    } else {
        Fail "PyTorch is not importable in .venv-sf3d."
    }
}

if (Test-Path $pythonExe) {
    & $pythonExe -c "import trimesh, rembg, huggingface_hub; print('dependencies-ok')" 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) {
        Pass "Core Stable Fast 3D Python dependencies are importable."
    } else {
        Fail "One or more Stable Fast 3D dependencies are missing. Rerun setup without -SkipRequirements."
    }
}

if (Test-Path $hfCli) {
    $whoami = & $hfCli whoami 2>$null
    if ($LASTEXITCODE -eq 0) {
        Pass "Hugging Face authentication is active: $($whoami -join ' ')"
    } else {
        Warn "Hugging Face authentication is not active. Run .\.venv-sf3d\Scripts\huggingface-cli.exe login after requesting model access."
    }
} else {
    Warn "huggingface-cli is not available yet."
}

if (Test-Path $envScript) {
    Pass "ARTIFEX environment script detected: .artifex\sf3d-env.ps1"
} else {
    Fail "ARTIFEX environment script is missing. Rerun setup."
}

if ($env:ARTIFEX_STABLE_FAST_3D_COMMAND -and $env:ARTIFEX_SF3D_REPO -and $env:ARTIFEX_SF3D_PYTHON) {
    Pass "Stable Fast 3D ARTIFEX environment variables are loaded in this PowerShell session."
} else {
    Warn "ARTIFEX environment variables are not loaded in this session. Run: . .\.artifex\sf3d-env.ps1"
}

if ($failed) {
    Write-Host "`nStable Fast 3D runtime check failed." -ForegroundColor Red
    exit 1
}

Write-Host "`nStable Fast 3D runtime check passed." -ForegroundColor Green
Write-Host "Next: load .artifex\sf3d-env.ps1, start the API/web app, then select Provider = Stable Fast 3D."
