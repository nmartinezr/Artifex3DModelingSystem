# Web Application

Primary responsibilities:

- User-facing ARTIFEX workflows.
- Image/model upload interaction.
- Three.js-based visualization and selection.
- Scene navigation and lightweight transforms.
- Tool parameter editing and manufacturing feedback.
- Display of geometry/printability findings and export results.

## Boundary

The web application must not own expensive geometry algorithms, AI inference or slicer execution. It communicates with the application API using versioned contracts and asset/resource identifiers.

All automatable interactive elements must expose stable `data-qa-id` attributes.
