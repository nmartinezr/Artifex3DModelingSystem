# Repository Structure

## Layering

ARTIFEX uses a monorepo with explicit runtime boundaries rather than a monolith of shared implementation details.

### `apps/web`
Presentation, visualization and interaction only. It may consume `api-contract` and safe `shared-types`, but must not import geometry engines, AI SDKs or slicer implementations.

### `apps/api`
Application orchestration boundary. It coordinates projects/assets and invokes service interfaces. It must not expose concrete engine/provider types through public contracts.

### `packages/project-schema`
Canonical project representation. This is one of the most stable contracts in the system and should evolve through explicit schema versions/migrations.

### `packages/api-contract`
Transport/application contracts. These are versioned independently from implementation details.

### `packages/shared-types`
Small, implementation-independent primitives only.

### `services/geometry-engine`
Computational geometry boundary. Initial Python implementation is expected, while the contract must permit native/C++/Rust replacements or accelerators later.

### `services/image-to-3d`
AI provider abstraction and generation orchestration. Provider SDK types never escape this service.

### `services/export-service`
Format adapters converting the canonical Project Model into manufacturing/interchange formats.

## Dependency Rules

Allowed high-level direction:

```text
web → api-contract/shared-types
api → project-schema/api-contract/shared-types + service interfaces
image-to-3d → project-schema/shared-types
geometry-engine → project-schema/shared-types
export-service → project-schema/shared-types
```

Forbidden examples:

- `web → trimesh/Open3D/TRELLIS`
- `project-schema → provider SDK`
- `api-contract → geometry-library native types`
- `export-service → ImageTo3DProvider implementation`

## Asset Strategy

Large images, meshes and textures are binary assets. Application messages reference them through asset/resource identifiers. This avoids repeatedly transferring millions of vertices as JSON and keeps API contracts stable.

## Replaceability

External engines are adapters. ARTIFEX owns its project model, operation semantics, diagnostics and manufacturing behavior; it does not allow a third-party provider's data model to become the system architecture.
