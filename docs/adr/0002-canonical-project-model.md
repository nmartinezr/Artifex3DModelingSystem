# ADR-0002: Canonical ARTIFEX Project Model

- Status: Accepted
- Date: 2026-08-30
- Issue: #2

## Context

ARTIFEX must process geometry from imported files and AI generation, allow non-destructive editing, perform manufacturing analysis and export to multiple formats. Using STL or any provider/library-native representation as the internal model would discard scene structure, materials, transforms, manufacturing intent and provenance.

## Decision

ARTIFEX will use a versioned provider-neutral Project Model whose top-level concepts are Project, Scene, SceneObject, Mesh asset reference, Transform, Material, ManufacturingData, Connectors, Analysis, OperationHistory and ExportConfiguration.

Large geometry and texture payloads are referenced by stable asset IDs instead of embedded in project JSON.

The initial contract is defined using JSON Schema Draft 2020-12 under `packages/project-schema/v1/project.schema.json`.

## Consequences

### Positive

- AI providers and geometry libraries remain replaceable.
- Multi-object assemblies and future rich 3MF export are supported from the beginning.
- Project persistence and API contracts can share one canonical domain model.
- Operation provenance and manufacturing analysis can be stored without mutating mesh formats.
- Tests can validate project state independently from UI and engine implementations.

### Trade-offs

- Importers/exporters require mapping layers.
- Referential integrity between IDs requires application-level validation in addition to JSON Schema.
- Schema migration must be maintained as the model evolves.

## Rejected alternatives

### STL as the internal representation
Rejected because STL contains essentially triangle geometry and cannot preserve object identity, transforms, materials, colors, textures or manufacturing metadata.

### GLB/3MF as the internal representation
Rejected as canonical application state. Both remain important interchange/export formats, but binding internal behavior directly to a file-format object model would unnecessarily couple editing and manufacturing workflows to serialization concerns.

### Geometry-library native objects
Rejected because this would leak implementation-specific types across service boundaries and make engine replacement significantly harder.
