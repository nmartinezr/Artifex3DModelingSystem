# ARTIFEX Project Model v1

## Purpose

The Project Model is the canonical internal representation for ARTIFEX. It represents editable scene state, manufacturing intent, analysis results, operation history and export preferences without coupling the application to STL, a geometry library, an AI provider or a slicer.

## Core invariants

1. `schemaVersion` is mandatory and currently fixed to `1.0.0`.
2. Manufacturing units are millimeters (`mm`).
3. A project owns a `Scene`; a scene owns zero or more independently addressable objects and materials.
4. Geometry is referenced through asset IDs. Large mesh payloads are not embedded directly in project JSON.
5. Every scene object has a stable `objectId`, transform and mesh reference.
6. Materials are independent entities and may include color and texture references.
7. Manufacturing metadata is explicit and extensible.
8. Analysis findings are structured and explainable; a score alone is never sufficient.
9. Operation history records reproducible intent and supports future undo/redo behavior.
10. Export configuration is project state, not UI-only state.

## Object identity and references

IDs are opaque stable strings. Cross-references such as `materialId`, `objectIds`, `inputObjectIds` and `outputObjectIds` must resolve inside the project domain or through the asset store as appropriate.

## Asset model

Mesh and texture payloads are stored outside the JSON project graph and referenced using `AssetReference`:

- `assetId`
- `mediaType`
- optional checksum
- optional byte length

This keeps API/project payloads small and allows the same asset to be used by viewers, geometry workers and exporters.

## Scene model

A `SceneObject` combines identity, transform, mesh reference, optional material and metadata. Multiple objects are first-class so splitting, assemblies, color-separated parts and future 3MF object mapping do not require redesigning the model.

## Transform model

Transforms are represented as translation + quaternion rotation + scale. Exact axis/handedness conventions are defined separately by the coordinate-system ADR/Issue #3.

## Manufacturing data

`ManufacturingData` stores manufacturing-specific intent and provides extension points for printer profiles, material strategies and later process-planning data. Vendor-specific slicer metadata must remain isolated from the canonical core.

## Connectors

Connector records are intentionally extensible. v1 requires connector identity, strategy/type and affected object IDs. Detailed connector geometry/tolerance schemas will evolve under the Manufacturing Tools milestone.

## Analysis

Analysis contains structured findings with stable codes, severity and user-facing explanations. Object-specific findings may reference an `objectId`.

## Operation history

Operations have stable IDs, types, status, parameters and optional input/output object references. Provider-specific Image → 3D provenance can live in operation metadata/parameters without leaking provider SDK types into the schema.

## Export configuration

v1 recognizes `3mf`, `glb` and `stl`. 3MF is the preferred manufacturing-rich format. STL remains supported as an interchange format but never becomes the canonical project model.

## Versioning and compatibility

- Patch/minor-compatible additions should use optional fields or extensible metadata.
- Breaking structural changes require a new major schema version and migration path.
- Unknown metadata may be preserved where schemas explicitly allow extension.
- Consumers must fail clearly on unsupported major versions rather than silently misinterpreting data.

## Validation fixtures

The schema includes examples for:

- a single AI-generated model with material and operation provenance;
- a multi-object assembly with separate transforms, materials and connector metadata.

These fixtures are intended to become executable schema/serialization tests once the package test runner is established.
