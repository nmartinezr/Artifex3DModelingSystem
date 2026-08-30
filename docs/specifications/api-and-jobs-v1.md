# API and Job Model v1

## Boundary
The web client communicates only with the ARTIFEX API. It never calls geometry or AI implementations directly.

## Binary asset strategy
Meshes, textures, uploaded images and generated binaries are stored as assets. JSON contracts carry stable asset IDs plus metadata; raw mesh payloads are not repeatedly serialized through REST/JSON.

## Long-running work
Image → 3D, expensive repair, slicing integrations and other non-trivial operations execute as jobs.

Job lifecycle:
`queued → running → succeeded | failed | cancelled`

Clients poll `/v1/jobs/{jobId}` initially. The contract permits a future event/SSE/WebSocket transport without changing job semantics.

## Error contract
Every public error contains:
- stable machine-readable `code`
- concise user-safe `message`
- `correlationId`
- optional structured `details`

Implementation stack traces, provider secrets and raw sensitive content must not cross the public API boundary.

## Initial technology choice
- API: Python 3.12 + FastAPI + Pydantic
- Geometry/AI service integration: Python service modules behind protocols/adapters
- Web: React + TypeScript + Three.js
- API description: OpenAPI 3.1

## Image → 3D vertical slice
1. upload source image as asset
2. create generation job
3. preprocess source
4. execute `IImageTo3DProvider`
5. normalize provider output
6. persist generated mesh/texture assets
7. create/update Project Model
8. perform basic validation
9. expose project/result to viewer
10. export GLB/STL/3MF through export service

## Versioning
Public API routes are prefixed `/v1`. Project/schema versions are independent of API versions. Breaking API changes require a new API major route or an explicitly versioned contract.
