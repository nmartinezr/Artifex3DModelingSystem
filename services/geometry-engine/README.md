# Geometry Engine

Provider-neutral geometry-processing boundary.

Planned capabilities include import inspection, transformations, connected-component analysis, validation, repair, cutting and export-oriented geometry conversion.

Concrete libraries such as trimesh, Open3D, libigl or CGAL must remain behind this boundary so application contracts do not depend on their native types.
