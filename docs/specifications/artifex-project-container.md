# `.artifex` Project Container v1

## Format
An `.artifex` file is a ZIP-compatible container. It separates human-readable project state from binary assets.

```text
project.artifex
├── manifest.json
├── project.json
├── assets/
│   ├── meshes/
│   ├── textures/
│   ├── images/
│   └── derived/
└── diagnostics/
    └── summary.json   (optional)
```

## `manifest.json`
Required fields:
- `format`: `artifex-project`
- `containerVersion`: semantic version
- `projectSchemaVersion`
- `projectId`
- `createdAt`
- `updatedAt`
- `assets[]`: asset ID, relative path, media type, size and SHA-256

## `project.json`
Must validate against the canonical ARTIFEX Project Model schema. It references binary assets exclusively by asset ID.

## Integrity
On load, ARTIFEX validates:
1. manifest syntax/version
2. supported project schema version
3. referenced asset existence
4. SHA-256 when present
5. project schema validity

The loader reports all recoverable findings. It must not partially overwrite an existing project when container validation fails.

## Versioning and migration
- Container and Project Model versions evolve independently.
- Minor/patch versions may add backward-compatible metadata.
- Unsupported major versions fail with `UNSUPPORTED_PROJECT_VERSION`.
- Migrations operate on a copy and produce a new canonical container; source files are never destructively rewritten without explicit save.

## Forward compatibility
Unknown metadata fields in designated extension maps are preserved where practical. Unknown required structural fields or unsupported operation versions must produce explicit diagnostics rather than silent data loss.

## Security
ZIP entry paths must be normalized and rejected if they escape the container root. Decompression size/count limits are mandatory to mitigate zip bombs. Executable content is never launched from a project container.
