# ARTIFEX 3D Modeling System

Manufacturing-first 3D preprocessing platform focused on turning images and 3D assets into printable, editable and reproducible manufacturing projects.

## Product direction

The first product vertical slice is:

```text
Image
  → Upload
  → Background Removal / Preprocessing
  → ImageTo3DProvider
  → Generated Mesh
  → ARTIFEX Project Model
  → 3D Viewer
  → Basic Geometry Validation
  → GLB / STL / 3MF Export
```

ARTIFEX is not intended to replace Blender, Fusion 360 or SolidWorks. Its focus is accessible automation and additive-manufacturing preparation.

## Local development quickstart

### Prerequisites

- Python 3.12+
- Node.js and npm
- Git

From the repository root, create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install the local Python services and API:

```bash
pip install -e "services/geometry-engine[dev]"
pip install -e "services/export-service[dev]"
pip install -e "apps/api[dev]"
```

Start the API from the repository root:

```bash
uvicorn artifex_api.main:app --reload --app-dir apps/api/src
```

Keep that terminal running. In a second terminal, start the web application:

```bash
cd apps/web
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally:

```text
http://localhost:5173
```

### What can be tested locally today

Select the `fixture` provider to exercise the complete GPU-free development flow:

```text
Image upload
  → preprocessing
  → deterministic fixture generation
  → persisted GLB
  → geometry validation
  → 3D viewer
  → GLB / STL / 3MF export
  → download
```

The `fixture` provider intentionally generates a deterministic cube. It validates the ARTIFEX application pipeline, geometry tooling and export workflow; it does **not** infer the uploaded image's shape.

### Real Image → 3D providers

ARTIFEX keeps inference engines behind the same `ImageTo3DProvider` boundary. The web UI currently exposes:

| Provider | Provider ID | Runner configuration |
| --- | --- | --- |
| Fixture | `fixture` | None; deterministic local/CI baseline |
| TRELLIS | `trellis` | `ARTIFEX_TRELLIS_COMMAND` |
| SPAR3D | `spar3d` | `ARTIFEX_SPAR3D_COMMAND` |
| Stable Fast 3D | `stable-fast-3d` | `ARTIFEX_STABLE_FAST_3D_COMMAND` |
| Hunyuan3D | `hunyuan3d` | `ARTIFEX_HUNYUAN3D_COMMAND` |

Real inference providers execute through isolated runner commands so GPU/model dependencies do not become dependencies of the ARTIFEX API process. Each runner receives an ARTIFEX request manifest and must return normalized mesh metadata/assets in millimeters, right-handed coordinates and Z-up convention.

Example TRELLIS configuration:

```bash
export ARTIFEX_TRELLIS_COMMAND="python /path/to/artifex_trellis_runner.py"
```

Windows PowerShell:

```powershell
$env:ARTIFEX_TRELLIS_COMMAND = "python C:\path\to\artifex_trellis_runner.py"
```

For CLI-based engines, `tools/image_to_3d/generic_cli_runner.py` can adapt an existing inference command that accepts an input image and writes a GLB. The runner environment must include `trimesh` in addition to the selected model's dependencies.

For example, after installing Stable Fast 3D in a separate environment:

```bash
export ARTIFEX_STABLE_FAST_3D_COMMAND='python tools/image_to_3d/generic_cli_runner.py --engine-command "python /opt/stable-fast-3d/run.py {input} --output-dir {engine_output}" --mesh-glob "**/mesh.glb"'
```

PowerShell uses the same runner with `$env:ARTIFEX_STABLE_FAST_3D_COMMAND = "..."`. The generic runner normalizes the largest model dimension to 100 mm by default, generates ARTIFEX geometry metrics and writes the common `result.json` contract. Use `--target-size-mm 0` when scale normalization should be disabled.

The equivalent provider environment variables can be configured for SPAR3D and Hunyuan3D using either the generic CLI runner or a provider-specific runner. Selecting an unconfigured provider returns a stable provider-unavailable error rather than silently falling back to another model.

See [Image → 3D Provider Benchmark](docs/image-to-3d/provider-benchmark.md) for the comparison criteria, runner contract and current provider recommendation. GPU-heavy benchmark runs are intentionally separate from normal CI; the deterministic fixture remains the default for smoke testing.

## Repository architecture

```text
apps/
  web/                  # React/TypeScript UI and 3D interaction
  api/                  # Application API and orchestration
packages/
  project-schema/       # Canonical ARTIFEX Project Model contracts
  api-contract/         # Versioned API request/response contracts
  shared-types/         # Cross-cutting types with no runtime coupling
services/
  geometry-engine/      # Geometry processing abstraction and adapters
  image-to-3d/          # Provider-neutral Image → 3D service
  export-service/       # STL, GLB and 3MF export adapters
tests/
  fixtures/             # Golden/regression assets
  geometry/             # Geometry property tests
  integration/          # Cross-service workflow tests
  e2e/                  # User-facing workflow automation
docs/
  architecture/         # Architecture documentation
  adr/                  # Architecture Decision Records
  specifications/       # Stable technical/product specifications
```

See [ADR-0001](docs/adr/0001-monorepo-architecture.md) for dependency rules and architectural rationale.

## Branch strategy

- `main`: stable/release-ready integration only.
- `develop`: primary integration branch.
- `feature/<issue>-<description>`: implementation branches targeting `develop`.

## Engineering principles

- The canonical internal model is never STL.
- Large mesh assets are referenced through asset/resource identifiers rather than repeatedly serialized as JSON.
- Heavy geometry processing stays outside the browser.
- AI engines and slicers are replaceable adapters behind stable interfaces.
- Deterministic processing is preferred whenever inference is not required.
- Manufacturing validity and printability are first-class concerns.
- Critical processing is testable independently of the UI.
- Automatable UI elements expose stable `data-qa-id` selectors.
