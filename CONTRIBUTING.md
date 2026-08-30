# Contributing to ARTIFEX

## Branch workflow
- `main`: stable/release-ready code
- `develop`: integration branch
- `feature/<issue>-<description>`: normal feature work
- `fix/<issue>-<description>`: defect work

Open pull requests into `develop`. Keep PRs linked to the corresponding Issue.

## Local API
```bash
cd apps/api
python -m venv .venv
# activate the virtual environment
pip install -e '.[dev]'
uvicorn artifex_api.main:app --reload
```

Run quality checks:
```bash
ruff check src tests
mypy src
pytest -q
```

## Local web
```bash
cd apps/web
npm install
npm run dev
```

Run quality checks:
```bash
npm run lint
npm run typecheck
npm test
npm run build
```

## Project schema
```bash
pip install -r packages/project-schema/requirements-dev.txt
python -m unittest discover -s packages/project-schema/tests -p 'test_*.py'
```

## Geometry engine and fixtures
```bash
pip install -e 'services/geometry-engine[dev]'
ruff check services/geometry-engine/src tests/geometry
mypy services/geometry-engine/src
pytest tests/geometry -q
python tests/geometry/benchmark_trimesh.py
```

## Pull Request requirements
- CI is green.
- Public contracts are updated when behavior changes.
- New UI controls/states intended for automation expose stable `data-qa-id` values.
- Geometry-changing features include semantic property tests/fixtures.
- New errors use stable machine-readable codes.
- No engine/provider-specific types leak into application contracts.
