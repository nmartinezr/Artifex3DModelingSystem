# ARTIFEX Engineering Standards

## Languages and runtime
- Web: TypeScript, React, Three.js
- API/services: Python 3.12+
- Geometry v1: trimesh behind ARTIFEX contracts
- API specification: OpenAPI 3.1
- Project contracts: JSON Schema Draft 2020-12

## Architecture rules
1. UI never owns expensive geometry algorithms.
2. Geometry, AI and slicer engines are adapters behind ARTIFEX interfaces.
3. Binary assets move by asset ID, not repeated JSON serialization.
4. Canonical Project Model is provider/engine/slicer neutral.
5. Manufacturing-impacting transformations are explicit and testable.

## Python
- Formatting/linting: Ruff
- Type checking: mypy for service contracts and core application code
- Tests: pytest/unittest-compatible tests
- Public APIs use type annotations.
- Domain errors use stable error codes, never string matching.

## TypeScript
- `strict: true`
- No `any` in public/shared contracts without documented justification.
- Component automation selectors use `data-qa-id`.
- Visible text, CSS classes and DOM position are not primary automation selectors.

## Testing layers
- unit: pure/domain behavior
- contract: Project Model/OpenAPI/provider/engine boundaries
- geometry-property: invariants such as watertightness, volume, component count, bounds
- integration: multi-service workflows
- E2E: critical user journeys only
- regression: every significant geometry/production defect adds a permanent fixture where practical

## Geometry assertions
Prefer semantic properties over exact binary equality:
- expected component count
- bounds within tolerance
- `volume > 0` where applicable
- watertight/manifold expectations
- no unexpected self-intersections/degenerate geometry when measurable
- correct units/orientation

## Observability
Every significant operation emits structured diagnostics including:
- correlation/job ID
- operation name/version
- durationMs
- input/output asset IDs
- triangle/vertex/component counts when relevant
- engine/provider and version
- normalized/sanitized parameters
- structured error code on failure

Never log secrets or raw private image/file content by default.

## Performance
- Never silently simplify source geometry.
- LOD/viewer proxies must be clearly separate from canonical assets.
- Expensive GPU/large-mesh tests are separated from fast PR CI.
- Resource limits fail explicitly with `RESOURCE_LIMIT_EXCEEDED` or a more specific stable code.

## Definition of Done
A feature is complete when its contract, error cases, appropriate automated tests, diagnostics and user-facing behavior are implemented. Geometry-changing behavior additionally requires fixture/property validation.
