"""GLB/glTF export of baked clips.

Writes node TRS animation tracks and mirrors only stable ids into glTF
``extras``. Blender-specific rig semantics are excluded; they live in the
sidecar manifest.

The writer is hand-rolled on stdlib ``struct``/``json`` rather than a glTF
library: the hard work (buffer packing, accessor bookkeeping) is ours either
way, and this keeps the deterministic core dependency-free. The GLB container
is a 12-byte header, a JSON chunk, and one binary chunk holding every accessor.

Layout contract: node 0 is the asset root (named after ``asset_id``); part
nodes follow in ``spec.parts`` order with identity rest transforms, parented
per the kinematic graph. Z-up specs get a -90 deg X rotation on the root so the
exported file is glTF Y-up; baked tracks live below the root and need no
conversion. Quaternions are glTF XYZW, matching the baker.
"""

from __future__ import annotations

import json
import math
import struct
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from mw_core.motion_spec.models import MotionSpec
from mw_core.rig.baker import BakedClip, TRSKeyframe
from mw_core.rig.kinematic_graph import KinematicGraph

_FLOAT32 = 5126
_UINT32 = 5125
_TRIANGLES = 4
_JSON_CHUNK = 0x4E4F534A  # 'JSON'
_BIN_CHUNK = 0x004E4942  # 'BIN\0'

# Animated TRS paths: glTF target path, accessor type, value extractor.
_TRS_PATHS: tuple[tuple[str, str, Callable[[TRSKeyframe], tuple[float, ...] | None]], ...] = (
    ("translation", "VEC3", lambda kf: kf.translation),
    ("rotation", "VEC4", lambda kf: kf.rotation_quat),
    ("scale", "VEC3", lambda kf: kf.scale),
)


class _BufferBuilder:
    """Accumulates the GLB binary chunk plus its bufferViews and accessors.

    Every accessor we emit has 4-byte components appended back to back, so
    offsets stay 4-byte aligned without explicit padding between views.
    """

    def __init__(self) -> None:
        self.data = bytearray()
        self.views: list[dict[str, Any]] = []
        self.accessors: list[dict[str, Any]] = []

    def _add_view(self, blob: bytes) -> int:
        self.views.append({"buffer": 0, "byteOffset": len(self.data), "byteLength": len(blob)})
        self.data.extend(blob)
        return len(self.views) - 1

    def add_float_accessor(
        self, rows: Sequence[Sequence[float]], gltf_type: str, *, with_min_max: bool = False
    ) -> int:
        flat = [float(c) for row in rows for c in row]
        blob = struct.pack(f"<{len(flat)}f", *flat)
        accessor: dict[str, Any] = {
            "bufferView": self._add_view(blob),
            "componentType": _FLOAT32,
            "count": len(rows),
            "type": gltf_type,
        }
        if with_min_max:
            # min/max must describe the float32-quantized values actually stored.
            rounded = struct.unpack(f"<{len(flat)}f", blob)
            width = len(rows[0])
            accessor["min"] = [min(rounded[i::width]) for i in range(width)]
            accessor["max"] = [max(rounded[i::width]) for i in range(width)]
        self.accessors.append(accessor)
        return len(self.accessors) - 1

    def add_uint_accessor(self, values: Sequence[int]) -> int:
        blob = struct.pack(f"<{len(values)}I", *values)
        self.accessors.append(
            {
                "bufferView": self._add_view(blob),
                "componentType": _UINT32,
                "count": len(values),
                "type": "SCALAR",
            }
        )
        return len(self.accessors) - 1


def _build_nodes(
    spec: MotionSpec,
    graph: KinematicGraph,
    part_index: dict[str, int],
    *,
    embed_stable_ids: bool,
) -> list[dict[str, Any]]:
    root: dict[str, Any] = {"name": spec.asset_id}
    up_axis = spec.coordinate_system.up_axis
    if up_axis == "Z":
        # Rotate the whole asset -90 deg about X so Z-up content is glTF Y-up.
        half = math.radians(-90.0) / 2.0
        root["rotation"] = [math.sin(half), 0.0, 0.0, math.cos(half)]
    elif up_axis != "Y":
        raise NotImplementedError(
            f"up_axis {up_axis!r} is not supported by the GLB exporter (only 'Z' and 'Y')"
        )
    scale = spec.coordinate_system.unit_scale_meters
    if scale != 1.0:
        root["scale"] = [scale, scale, scale]

    nodes = [root]
    for part in spec.parts:
        node: dict[str, Any] = {"name": part.name}
        if embed_stable_ids:
            node["extras"] = {"mw_part_id": part.id}
        nodes.append(node)

    # glTF forbids empty children arrays, so set them only when populated.
    if graph.roots:
        root["children"] = [part_index[r.part_id] for r in graph.roots]
    for gnode in graph.iter_nodes():
        if gnode.children:
            nodes[part_index[gnode.part_id]]["children"] = [
                part_index[child.part_id] for child in gnode.children
            ]
    return nodes


def _build_meshes(
    spec: MotionSpec,
    meshes: Mapping[str, Any],
    part_index: dict[str, int],
    nodes: list[dict[str, Any]],
    buffer: _BufferBuilder,
) -> list[dict[str, Any]]:
    unknown = sorted(set(meshes) - set(part_index))
    if unknown:
        raise ValueError(f"meshes provided for unknown part ids: {unknown}")
    mesh_dicts: list[dict[str, Any]] = []
    for part in spec.parts:
        mesh = meshes.get(part.id)
        if mesh is None:
            continue
        positions = [tuple(float(c) for c in vertex) for vertex in mesh.vertices]
        position_acc = buffer.add_float_accessor(positions, "VEC3", with_min_max=True)
        indices_acc = buffer.add_uint_accessor([int(i) for face in mesh.faces for i in face])
        mesh_dicts.append(
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": position_acc},
                        "indices": indices_acc,
                        "mode": _TRIANGLES,
                    }
                ]
            }
        )
        nodes[part_index[part.id]]["mesh"] = len(mesh_dicts) - 1
    return mesh_dicts


def _build_animations(
    baked_clips: list[BakedClip],
    part_index: dict[str, int],
    buffer: _BufferBuilder,
) -> list[dict[str, Any]]:
    animations: list[dict[str, Any]] = []
    for clip in baked_clips:
        samplers: list[dict[str, Any]] = []
        channels: list[dict[str, Any]] = []
        for track in clip.tracks:
            if not track.keyframes:
                continue
            node = part_index.get(track.part_id)
            if node is None:
                raise ValueError(f"baked track references unknown part {track.part_id!r}")
            input_acc = buffer.add_float_accessor(
                [(kf.t,) for kf in track.keyframes], "SCALAR", with_min_max=True
            )
            for path, gltf_type, extract in _TRS_PATHS:
                values = [extract(kf) for kf in track.keyframes]
                if all(v is None for v in values):
                    continue
                if any(v is None for v in values):
                    raise ValueError(
                        f"track {track.part_id!r} mixes keyframes with and without {path} values"
                    )
                present = [v for v in values if v is not None]
                output_acc = buffer.add_float_accessor(present, gltf_type)
                samplers.append(
                    {"input": input_acc, "output": output_acc, "interpolation": "LINEAR"}
                )
                channels.append(
                    {"sampler": len(samplers) - 1, "target": {"node": node, "path": path}}
                )
        if channels:
            animations.append({"name": clip.clip_id, "samplers": samplers, "channels": channels})
    return animations


def export_glb(
    out_path: str | Path,
    spec: MotionSpec,
    graph: KinematicGraph,
    baked_clips: list[BakedClip],
    *,
    meshes: Mapping[str, Any] | None = None,
    embed_stable_ids: bool = True,
) -> Path:
    """Write a ``.glb`` with the part-node hierarchy and baked TRS animation tracks.

    Each BakedClip becomes a glTF animation; each BakedTrack maps to TRS channels
    on the corresponding part node. ``meshes`` optionally maps part ids to
    trimesh-like objects (``.vertices``/``.faces``) attached to their nodes. When
    ``embed_stable_ids`` is set, part ids are mirrored into node ``extras``
    (stable ids only, never the canonical semantics — those live in the manifest).
    """
    part_index = {part.id: i + 1 for i, part in enumerate(spec.parts)}
    buffer = _BufferBuilder()

    nodes = _build_nodes(spec, graph, part_index, embed_stable_ids=embed_stable_ids)
    mesh_dicts = _build_meshes(spec, meshes or {}, part_index, nodes, buffer)
    animations = _build_animations(baked_clips, part_index, buffer)

    doc: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": "MotionWeaver"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": nodes,
    }
    if mesh_dicts:
        doc["meshes"] = mesh_dicts
    if animations:
        doc["animations"] = animations
    if buffer.accessors:
        doc["accessors"] = buffer.accessors
        doc["bufferViews"] = buffer.views
        doc["buffers"] = [{"byteLength": len(buffer.data)}]

    json_bytes = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)
    binary = bytes(buffer.data) + b"\0" * (-len(buffer.data) % 4)

    total = 12 + 8 + len(json_bytes) + (8 + len(binary) if binary else 0)
    path = Path(out_path)
    with path.open("wb") as fh:
        fh.write(struct.pack("<4sII", b"glTF", 2, total))
        fh.write(struct.pack("<II", len(json_bytes), _JSON_CHUNK))
        fh.write(json_bytes)
        if binary:
            fh.write(struct.pack("<II", len(binary), _BIN_CHUNK))
            fh.write(binary)
    return path
