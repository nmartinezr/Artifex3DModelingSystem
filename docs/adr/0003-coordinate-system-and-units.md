# ADR-0003 — Coordinate System and Unit Conventions

Status: Accepted

## Decision
ARTIFEX uses a **right-handed Cartesian coordinate system** internally.

- Units: **millimeters (mm)**
- X axis: positive to the right
- Y axis: positive to the back
- Z axis: positive upward
- Up axis: **+Z**
- Forward direction for presentation/import normalization: **-Y**
- Origin: model-space origin; individual objects own local transforms relative to the project scene
- Angles: radians internally; UI may display degrees
- Transform order: scale → rotation → translation
- Matrices: 4×4 homogeneous matrices using column vectors; transforms compose right-to-left
- Quaternions: `[x, y, z, w]`

## Manufacturing convention
All physical dimensions stored in the canonical Project Model are millimeters. Any source lacking explicit units must pass through an importer policy; ARTIFEX must never silently reinterpret unknown units.

## Import normalization
Each importer/provider adapter is responsible for converting source axes, handedness and units into ARTIFEX canonical coordinates before geometry is interpreted as manufacturing data.

Examples:
- glTF/GLB defines linear distances in **meters** and uses a right-handed coordinate system with +Y up. ARTIFEX converts meters → millimeters and maps the external orientation into canonical +Z-up coordinates at the adapter boundary.
- STL has no reliable unit metadata; import requires a declared/default policy and records the decision in provenance metadata.
- 3MF explicitly declares a model unit. ARTIFEX converts that unit to millimeters on import; ARTIFEX manufacturing export writes `unit="millimeter"` explicitly.
- AI provider output is treated as provider-native until its adapter normalizes it.

## Export
Export adapters perform the inverse mapping required by the target format without mutating canonical project state.

- GLB/glTF writers convert canonical millimeters → meters.
- STL writers emit numeric dimensions in millimeters by ARTIFEX manufacturing convention and must communicate that STL itself does not encode units.
- 3MF writers declare `millimeter` explicitly in the model part.

Existing GLB assets may be passed through unchanged when no canonical geometry operation has modified them. Validation and analysis still report physical dimensions in millimeters.

## Determinism requirements
- Identical source geometry + identical import policy must produce identical canonical coordinates.
- Round-trip tests compare dimensions, bounds and orientation within format-specific tolerances.
- No implicit axis swap, mirror or scale is allowed outside adapter boundaries.
- Tests covering GLB must assert meter ↔ millimeter conversion explicitly; a numerically correct mesh at the wrong physical scale is a failed round trip.

## Rationale
A manufacturing system cannot tolerate hidden unit or orientation conversions. Fixing these conventions prevents subtle failures in Image → 3D, transforms, splitting, connectors, 3MF export and slicer integration.
