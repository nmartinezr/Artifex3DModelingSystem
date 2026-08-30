# Project Schema

Versioned canonical ARTIFEX Project Model contracts.

The schema remains independent from STL and from any specific AI, geometry or slicer implementation.

## v1

The initial contract lives at:

```text
v1/project.schema.json
```

It defines the core concepts:

- Project
- Scene and SceneObject
- Mesh asset references
- Transform
- Material and color/texture metadata
- ManufacturingData
- Connectors
- Analysis findings
- OperationHistory
- ExportConfiguration

Binary meshes and textures are referenced by asset IDs instead of being embedded in project JSON.

## Validation fixtures

Representative valid projects are stored under:

```text
v1/examples/
```

Current fixtures cover a single AI-generated object and a multi-object manufacturing assembly.

## Run schema tests

```bash
python -m pip install -r packages/project-schema/requirements-dev.txt
python -m unittest discover -s packages/project-schema/tests -p "test_*.py"
```

The test suite validates the JSON Schema itself, verifies the example fixtures, and checks rejection of unsupported schema versions and missing required project structure.

## Design documentation

See:

- `docs/specifications/project-model-v1.md`
- `docs/adr/0002-canonical-project-model.md`
