# Contributing to ARTIFEX

## Branch workflow
- `main`: stable/release-ready code
- `develop`: integration branch
- `feature/<issue>-<description>`: normal feature work
- `fix/<issue>-<description>`: defect work

Open pull requests into `develop`. Keep PRs linked to the corresponding Issue.

## Local environment
Create one Python virtual environment from the repository root so the monorepo services are available to the API:

```bash
python -m venv .venv
# activate the virtual environment
pip install -e 'services/geometry-engine[dev]'
pip install -e 'services/export-service[dev]'
pip install -e 'apps/api[dev]'
```

Start the API:

```bash
uvicorn artifex_api.main:app --reload --app-dir apps/api/src
```

The API is available at `http://127.0.0.1:8000`.

Start the web application in another terminal:

```bash
cd apps/web
npm install
npm run dev
```

The Vite application normally runs at `http://127.0.0.1:5173` or `http://localhost:5173`.

## Local Image → 3D demo
The default `Fixture` provider is intentionally GPU-free. It exercises the real application path:

```text
image upload
→ preprocessing
→ provider dispatch
→ persisted GLB
→ geometry validation
→ Three.js viewer
→ GLB / STL / 3MF export
```

The fixture provider emits deterministic geometry rather than inferring the uploaded object's shape. Use it to verify application plumbing, UI behavior, validation and export without model weights.

To use the real TRELLIS adapter, configure a compatible external runner before starting the API:

```bash
# Example only; point this to the runner installed on your machine/GPU environment.
export ARTIFEX_TRELLIS_COMMAND="python /path/to/artifex_trellis_runner.py"
```

On Windows PowerShell:

```powershell
$env:ARTIFEX_TRELLIS_COMMAND = "python C:\path\to\artifex_trellis_runner.py"
```

## API quality checks
From `apps/api` after installing the monorepo services:

```bash
ruff check src tests
mypy src
pytest -q
```

## Web quality checks
From `apps/web`:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

## Project schema
From repository root:

```bash
pip install -r packages/project-schema/requirements-dev.txt
python -m unittest discover -s packages/project-schema/tests -p 'test_*.py'
```

## Geometry engine and fixtures
From repository root:

```bash
ruff check services/geometry-engine/src tests/geometry
mypy services/geometry-engine/src
pytest tests/geometry -q
python tests/geometry/benchmark_trimesh.py
```

## Export service
From repository root:

```bash
ruff check services/export-service/src tests/export
mypy services/export-service/src
pytest tests/export -q
```

## Pull Request requirements
- CI is green.
- Public contracts are updated when behavior changes.
- New UI controls/states intended for automation expose stable `data-qa-id` values.
- Geometry-changing features include semantic property tests/fixtures.
- New errors use stable machine-readable codes.
- No engine/provider-specific types leak into application contracts.
- Unit/coordinate conversion is explicit at format boundaries; ARTIFEX uses millimeters internally while glTF/GLB uses meters.
