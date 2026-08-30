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
