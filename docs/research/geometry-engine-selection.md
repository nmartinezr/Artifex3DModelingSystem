# Geometry Engine Selection — M0

## Decision
Use **trimesh** as the initial ARTIFEX mesh-processing implementation behind `GeometryEngine`. Add **Open3D** only when its algorithms provide clear value. Keep **libigl** and **CGAL** as future native-engine candidates behind the same contracts.

## Evaluation summary

| Candidate | Initial role | Strengths | Constraints / risk |
|---|---|---|---|
| trimesh | Primary v1 engine | Python-native integration, mesh inspection, watertightness, scenes/transforms, import/export, booleans through mature backends, permissive MIT license | Some heavy operations rely on optional/native backends |
| Open3D | Optional complementary engine | Strong 3D processing toolkit, point clouds, reconstruction, Python/C++, MIT license | Larger dependency footprint; not necessary for every mesh operation |
| libigl | Future advanced/native engine | High-quality geometry-processing algorithms, C++ foundation | Primary license MPL-2.0; third-party/copyleft components require per-feature review |
| CGAL | Future specialized engine | Robust computational geometry and exact algorithms | GPL/LGPL/commercial licensing requires careful component-level legal review |

## Why trimesh first
ARTIFEX's first vertical slice needs deterministic mesh loading, inspection, transforms, connected components, basic repair hooks, bounds/volume metrics and export support. Trimesh provides these capabilities with the lowest integration cost and a permissive license while keeping the architecture replaceable.

## Dependency rule
No application-level contract may expose `trimesh.Trimesh`, `open3d.geometry.*`, Eigen matrices, CGAL types or another implementation-specific object. Engines convert to/from ARTIFEX-owned DTOs/assets at the boundary.

## Benchmark plan
Before replacing or adding an engine, run the common fixture suite against:
- valid cube and sphere
- thin-wall object
- non-manifold mesh
- open mesh / holes
- disconnected components
- degenerate triangles
- representative character mesh
- high-poly mesh

Measure load time, operation time, peak memory where practical, triangle/component counts, watertight/manifold results and output invariants.

## Licensing gate
Every optional native dependency must be reviewed before production adoption. A dependency that forces redistribution/source obligations inconsistent with ARTIFEX distribution must not be introduced silently; either isolate it appropriately, use a commercial license, or select an alternative.
