# Application API

Primary responsibilities:

- Workflow orchestration.
- Authentication/authorization boundary when introduced.
- Asset lifecycle coordination.
- Project-model persistence coordination.
- Geometry service orchestration.
- Image-to-3D job orchestration.
- Export orchestration.
- Structured error/diagnostic translation.

## Boundary

The API must depend on stable contracts rather than concrete provider SDKs or geometry-library types.
