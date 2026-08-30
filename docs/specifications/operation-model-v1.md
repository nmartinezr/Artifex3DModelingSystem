# ARTIFEX Operation Model v1

## Purpose
Represent editing and manufacturing operations as reproducible project state instead of destructive mesh mutations.

## Operation record
Every operation contains:
- `id`: stable UUID
- `type`: namespaced operation identifier, e.g. `transform.scale`, `geometry.planar-cut`, `connector.cylindrical-pin`
- `version`: operation contract version
- `inputObjectIds`: project objects consumed/read
- `parameters`: normalized, serializable parameters
- `outputObjectIds`: objects produced or updated
- `status`: `pending | applied | failed | invalidated`
- `createdAt`
- `engine`: optional implementation provenance
- `diagnostics`: structured warnings/errors

## Execution semantics
1. Operations read immutable input asset versions.
2. Successful geometry-changing operations produce new asset versions.
3. Project object references are advanced atomically only after successful execution.
4. A failed operation cannot corrupt the last valid state.
5. Downstream operations are invalidated when an upstream parameter or input changes.
6. Replay uses the same canonical parameters and coordinate conventions.

## Undo / redo
Undo moves the project head to the previous applied operation state; it does not delete historical records. Redo reapplies a previously valid state when its dependencies remain unchanged.

## Determinism
Deterministic operations must produce semantically equivalent geometry for identical inputs and engine versions. AI generation is explicitly non-deterministic unless the provider supports reproducible seeds; its provenance therefore records provider, model/version, seed when available and sanitized parameters.

## Example
```json
{
  "id": "op-003",
  "type": "geometry.planar-cut",
  "version": "1.0.0",
  "inputObjectIds": ["object-body"],
  "parameters": {
    "originMm": [0, 0, 42],
    "normal": [0, 0, 1]
  },
  "outputObjectIds": ["object-body-a", "object-body-b"],
  "status": "applied"
}
```

## Invariants
- No operation stores raw mesh bytes in project JSON.
- Operation parameters use ARTIFEX canonical mm/+Z-up conventions.
- Engine/provider-native objects never appear in the persisted contract.
- Every material geometry change that affects manufacturing must be visible in history.
