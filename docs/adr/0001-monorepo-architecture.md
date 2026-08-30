# ADR-0001: Monorepo Architecture and Service Boundaries

- Status: Accepted
- Issue: #1

## Context

ARTIFEX combines browser-based 3D interaction, application orchestration, computational geometry, AI-based Image → 3D generation, manufacturing analysis and format/slicer integration. These areas have different runtime and dependency requirements.

The first product vertical slice must support Image upload → Image-to-3D generation → canonical Project Model → browser viewer → geometry validation → GLB/STL/3MF export without coupling the entire product to a single AI or geometry engine.

## Decision

Use a monorepo with three explicit categories:

1. `apps/` for deployable user/application surfaces.
2. `packages/` for stable implementation-independent contracts.
3. `services/` for replaceable computational/provider capabilities.

Tests and architecture documentation remain top-level concerns.

The primary frontend candidate is React + TypeScript + Three.js. Python is the initial candidate for geometry and AI integration. Native implementations can be introduced behind service interfaces when profiling demonstrates a need.

## Consequences

### Positive

- Shared contracts can evolve atomically with consuming applications.
- Provider and geometry dependencies are isolated.
- The Image → 3D vertical slice can be built without making provider output canonical.
- QA fixtures and integration tests can span the complete workflow in one repository.
- Native acceleration can be introduced later without changing frontend contracts.

### Trade-offs

- Build tooling must coordinate TypeScript and Python ecosystems.
- Contract ownership must be enforced to prevent inappropriate cross-module imports.
- Monorepo CI requires selective/parallel test execution as the project grows.

## Architectural Constraints

- STL is never the canonical internal representation.
- Complex geometry computation does not live in the browser by default.
- AI providers are replaceable adapters.
- Slicers are integrations, not functionality ARTIFEX reimplements.
- Binary assets are referenced through IDs rather than continuously serialized in API JSON.
- Critical processing must be testable without UI automation.
- UI automation uses `data-qa-id` selectors.

## Validation Against First Vertical Slice

```text
apps/web
  ↓ api-contract
apps/api
  ↓
services/image-to-3d
  ↓
packages/project-schema
  ↓
services/geometry-engine
  ↓
services/export-service
```

The architecture therefore supports the first product objective while preserving future manufacturing, color, connector and printability capabilities.
