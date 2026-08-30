from __future__ import annotations

import json
import struct


def create_fixture_cube_glb(size_mm: float = 40.0) -> bytes:
    """Create a valid deterministic GLB cube for local/CI Image → 3D flows."""
    half = size_mm / 2.0
    faces = (
        ((0.0, 0.0, 1.0), ((-half, -half, half), (half, -half, half), (half, half, half), (-half, half, half))),
        ((0.0, 0.0, -1.0), ((-half, half, -half), (half, half, -half), (half, -half, -half), (-half, -half, -half))),
        ((1.0, 0.0, 0.0), ((half, -half, -half), (half, half, -half), (half, half, half), (half, -half, half))),
        ((-1.0, 0.0, 0.0), ((-half, -half, half), (-half, half, half), (-half, half, -half), (-half, -half, -half))),
        ((0.0, 1.0, 0.0), ((-half, half, half), (half, half, half), (half, half, -half), (-half, half, -half))),
        ((0.0, -1.0, 0.0), ((-half, -half, -half), (half, -half, -half), (half, -half, half), (-half, -half, half))),
    )

    positions: list[float] = []
    normals: list[float] = []
    indices: list[int] = []
    for face_index, (normal, vertices) in enumerate(faces):
        base = face_index * 4
        for vertex in vertices:
            positions.extend(vertex)
            normals.extend(normal)
        indices.extend((base, base + 1, base + 2, base, base + 2, base + 3))

    position_bytes = struct.pack(f"<{len(positions)}f", *positions)
    normal_bytes = struct.pack(f"<{len(normals)}f", *normals)
    index_bytes = struct.pack(f"<{len(indices)}H", *indices)
    binary = position_bytes + normal_bytes + index_bytes
    binary += b"\x00" * ((4 - len(binary) % 4) % 4)

    gltf = {
        "asset": {"version": "2.0", "generator": "ARTIFEX deterministic fixture provider"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "ARTIFEX Fixture Cube"}],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "NORMAL": 1},
                        "indices": 2,
                        "material": 0,
                        "mode": 4,
                    }
                ]
            }
        ],
        "materials": [
            {
                "name": "ARTIFEX Fixture Material",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.55, 0.32, 0.95, 1.0],
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.65,
                },
            }
        ],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(position_bytes), "target": 34962},
            {
                "buffer": 0,
                "byteOffset": len(position_bytes),
                "byteLength": len(normal_bytes),
                "target": 34962,
            },
            {
                "buffer": 0,
                "byteOffset": len(position_bytes) + len(normal_bytes),
                "byteLength": len(index_bytes),
                "target": 34963,
            },
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 24,
                "type": "VEC3",
                "min": [-half, -half, -half],
                "max": [half, half, half],
            },
            {"bufferView": 1, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5123, "count": 36, "type": "SCALAR"},
        ],
    }

    json_chunk = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)

    total_length = 12 + 8 + len(json_chunk) + 8 + len(binary)
    header = struct.pack("<4sII", b"glTF", 2, total_length)
    json_header = struct.pack("<II", len(json_chunk), 0x4E4F534A)
    binary_header = struct.pack("<II", len(binary), 0x004E4942)
    return header + json_header + json_chunk + binary_header + binary
