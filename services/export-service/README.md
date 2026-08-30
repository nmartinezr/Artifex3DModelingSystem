# Export Service

Format-specific manufacturing export adapters for ARTIFEX projects. Export logic is independent from Image → 3D providers and consumes ARTIFEX-owned mesh assets.

## Format boundaries

ARTIFEX canonical geometry uses millimeters and a right-handed Z-up convention. External formats are normalized explicitly:

- **GLB/glTF** — glTF linear distances are meters. ARTIFEX converts millimeters to meters when creating a new GLB. Existing generated GLB assets are passed through when possible so materials/textures are not unnecessarily rewritten.
- **STL** — ARTIFEX writes manufacturing dimensions in millimeters by convention. STL carries mesh geometry only; color, material and texture information is not preserved.
- **3MF** — ARTIFEX writes `unit="millimeter"` explicitly and produces a standards-based package.

No exporter may silently infer or change canonical scale.

## M1 3MF scope

The initial adapter produces one mesh/object with:

- `[Content_Types].xml`
- `_rels/.rels`
- `3D/3dmodel.model`
- explicit millimeter units
- vertices and triangles
- one build item

ZIP entry timestamps are fixed so identical input produces deterministic bytes.

Future versions extend this service, rather than provider code, with:

- multiple objects and transforms
- colors/materials
- manufacturing strategy metadata
- slicer/profile metadata
- Bambu Studio / OrcaSlicer / PrusaSlicer compatibility adapters where justified

Vendor-specific metadata must remain isolated from the canonical Project Model and standards-based 3MF path.

## Quality gate

Application orchestration runs non-mutating geometry validation before manufacturing export. Severe findings can block export; warnings remain visible to the user without automatically altering the source mesh.
