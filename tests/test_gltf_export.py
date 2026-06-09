"""GLB export: container format, node hierarchy, meshes, and baked animations."""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path
from typing import Any

import pytest

from conftest import make_spec
from mw_core import MotionSpec, normalize_spec, validate_spec
from mw_core.exporters.gltf_export import export_glb
from mw_core.rig.baker import BakedClip, BakedTrack, TRSKeyframe, bake
from mw_core.rig.planner import plan

_JSON_CHUNK = 0x4E4F534A  # 'JSON'
_BIN_CHUNK = 0x004E4942  # 'BIN\0'


def _read_glb(path: Path) -> tuple[dict[str, Any], bytes]:
    """Parse a GLB container: header + JSON chunk + optional BIN chunk."""
    data = path.read_bytes()
    assert data[0:4] == b"glTF"
    version, total_length = struct.unpack_from("<II", data, 4)
    assert version == 2
    assert total_length == len(data)
    json_length, json_type = struct.unpack_from("<II", data, 12)
    assert json_type == _JSON_CHUNK
    doc = json.loads(data[20 : 20 + json_length].decode("utf-8"))
    offset = 20 + json_length
    binary = b""
    if offset < len(data):
        bin_length, bin_type = struct.unpack_from("<II", data, offset)
        assert bin_type == _BIN_CHUNK
        binary = bytes(data[offset + 8 : offset + 8 + bin_length])
    return doc, binary


def _accessor_values(
    doc: dict[str, Any], binary: bytes, accessor_index: int
) -> list[tuple[float, ...]] | list[float]:
    """Decode an accessor's values from the binary chunk."""
    accessor = doc["accessors"][accessor_index]
    view = doc["bufferViews"][accessor["bufferView"]]
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    component_count = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    fmt = {5126: "f", 5125: "I"}[accessor["componentType"]]
    flat = struct.unpack_from(f"<{accessor['count'] * component_count}{fmt}", binary, offset)
    if component_count == 1:
        return list(flat)
    return [tuple(flat[i : i + component_count]) for i in range(0, len(flat), component_count)]


def _channel_outputs(
    doc: dict[str, Any], binary: bytes, animation: dict[str, Any]
) -> dict[str, Any]:
    """Map target path -> (target node, sampler interpolation, input values, output values)."""
    out: dict[str, Any] = {}
    for channel in animation["channels"]:
        sampler = animation["samplers"][channel["sampler"]]
        out[channel["target"]["path"]] = {
            "node": channel["target"]["node"],
            "interpolation": sampler["interpolation"],
            "input": _accessor_values(doc, binary, sampler["input"]),
            "output": _accessor_values(doc, binary, sampler["output"]),
        }
    return out


def test_glb_container_and_node_hierarchy(
    tmp_path: Path, antenna_spec_dict: dict[str, Any]
) -> None:
    spec = validate_spec(normalize_spec(MotionSpec.model_validate(antenna_spec_dict)))
    out = export_glb(tmp_path / "antenna.glb", spec, plan(spec), [])
    doc, _ = _read_glb(out)
    assert doc["asset"]["version"] == "2.0"
    assert doc["scenes"][doc["scene"]]["nodes"] == [0]
    nodes = doc["nodes"]
    # Node 0 is the asset root; parts follow in spec order.
    assert len(nodes) == 6
    assert nodes[0]["name"] == "antenna_demo_a01"
    assert [n["name"] for n in nodes[1:]] == ["Base", "Mast", "Dish Yoke", "Dish", "Service Hatch"]
    # Hierarchy mirrors the kinematic graph: base and dish_yoke are roots.
    assert nodes[0]["children"] == [1, 3]
    assert nodes[1]["children"] == [2, 5]
    assert nodes[3]["children"] == [4]
    # Stable ids are mirrored into extras by default.
    assert nodes[1]["extras"]["mw_part_id"] == "base"
    # No clips and no meshes were given.
    assert "animations" not in doc
    assert "meshes" not in doc


def test_zup_spec_gets_yup_conversion_rotation_on_root(tmp_path: Path) -> None:
    spec = make_spec(up_axis="Z")
    out = export_glb(tmp_path / "zup.glb", spec, plan(spec), [])
    doc, _ = _read_glb(out)
    half = math.radians(-90.0) / 2
    assert doc["nodes"][0]["rotation"] == pytest.approx([math.sin(half), 0.0, 0.0, math.cos(half)])


def test_yup_spec_root_has_no_rotation(tmp_path: Path) -> None:
    spec = make_spec(up_axis="Y")
    out = export_glb(tmp_path / "yup.glb", spec, plan(spec), [])
    doc, _ = _read_glb(out)
    assert "rotation" not in doc["nodes"][0]


def test_unsupported_up_axis_is_rejected(tmp_path: Path) -> None:
    spec = make_spec(up_axis="X")
    with pytest.raises(NotImplementedError, match="up_axis"):
        export_glb(tmp_path / "xup.glb", spec, plan(spec), [])


def test_unit_scale_is_applied_to_root(tmp_path: Path) -> None:
    spec = make_spec(unit_scale_meters=2.0)
    out = export_glb(tmp_path / "scaled.glb", spec, plan(spec), [])
    doc, _ = _read_glb(out)
    assert doc["nodes"][0]["scale"] == pytest.approx([2.0, 2.0, 2.0])

    spec = make_spec(unit_scale_meters=1.0)
    out = export_glb(tmp_path / "unscaled.glb", spec, plan(spec), [])
    doc, _ = _read_glb(out)
    assert "scale" not in doc["nodes"][0]


def test_embed_stable_ids_false_omits_extras(tmp_path: Path) -> None:
    spec = make_spec()
    out = export_glb(tmp_path / "noids.glb", spec, plan(spec), [], embed_stable_ids=False)
    doc, _ = _read_glb(out)
    assert all("extras" not in node for node in doc["nodes"])


def test_hinge_animation_has_translation_and_rotation_channels(tmp_path: Path) -> None:
    spec = make_spec(
        axis=[0.0, 0.0, 1.0], pivot=[1.0, 0.0, 0.0], keyframes=[(0.0, 0.0), (1.0, 90.0)]
    )
    baked = bake(spec, plan(spec), sample_rate_hz=1.0)
    out = export_glb(tmp_path / "hinge.glb", spec, plan(spec), baked)
    doc, binary = _read_glb(out)
    (animation,) = doc["animations"]
    assert animation["name"] == "clip1"
    channels = _channel_outputs(doc, binary, animation)
    assert set(channels) == {"translation", "rotation"}
    # Both channels target the "arm" node (root=0, base=1, arm=2) with LINEAR samplers.
    for path_data in channels.values():
        assert path_data["node"] == 2
        assert path_data["interpolation"] == "LINEAR"
        assert path_data["input"] == pytest.approx([0.0, 1.0])
    half = math.radians(90.0) / 2
    assert channels["rotation"]["output"][0] == pytest.approx((0.0, 0.0, 0.0, 1.0))
    assert channels["rotation"]["output"][1] == pytest.approx(
        (0.0, 0.0, math.sin(half), math.cos(half))
    )
    assert channels["translation"]["output"][1] == pytest.approx((1.0, -1.0, 0.0))
    # Animation sampler input accessors must declare min/max per the glTF spec.
    input_accessor = doc["accessors"][animation["samplers"][0]["input"]]
    assert input_accessor["min"] == pytest.approx([0.0])
    assert input_accessor["max"] == pytest.approx([1.0])


def test_slider_animation_emits_translation_only(tmp_path: Path) -> None:
    spec = make_spec(
        joint_type="slider",
        axis=[0.0, 0.0, 1.0],
        control_property="distance_m",
        keyframes=[(0.0, 0.0), (1.0, 0.5)],
    )
    baked = bake(spec, plan(spec), sample_rate_hz=1.0)
    out = export_glb(tmp_path / "slider.glb", spec, plan(spec), baked)
    doc, binary = _read_glb(out)
    channels = _channel_outputs(doc, binary, doc["animations"][0])
    assert set(channels) == {"translation"}
    assert channels["translation"]["output"][1] == pytest.approx((0.0, 0.0, 0.5))


def test_meshes_attach_to_part_nodes_and_load_in_trimesh(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    spec = make_spec()
    meshes = {
        "base": trimesh.creation.box(extents=(1.0, 1.0, 1.0)),
        "arm": trimesh.creation.box(extents=(0.2, 0.2, 2.0)),
    }
    out = export_glb(tmp_path / "boxes.glb", spec, plan(spec), [], meshes=meshes)
    doc, _ = _read_glb(out)
    assert "mesh" in doc["nodes"][1]
    assert "mesh" in doc["nodes"][2]
    # POSITION accessors must declare min/max per the glTF spec.
    for mesh in doc["meshes"]:
        position_accessor = doc["accessors"][mesh["primitives"][0]["attributes"]["POSITION"]]
        assert len(position_accessor["min"]) == 3
        assert len(position_accessor["max"]) == 3
    # The exported file is a valid GLB that trimesh can load back.
    scene = trimesh.load(out)
    assert len(scene.geometry) == 2
    assert sum(len(g.vertices) for g in scene.geometry.values()) == 16


def test_mesh_for_unknown_part_is_rejected(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    spec = make_spec()
    meshes = {"ghost": trimesh.creation.box(extents=(1.0, 1.0, 1.0))}
    with pytest.raises(ValueError, match="ghost"):
        export_glb(tmp_path / "ghost.glb", spec, plan(spec), [], meshes=meshes)


def test_track_for_unknown_part_is_rejected(tmp_path: Path) -> None:
    spec = make_spec()
    clip = BakedClip(
        clip_id="bad",
        tracks=[BakedTrack(part_id="ghost", keyframes=[TRSKeyframe(t=0.0)])],
    )
    with pytest.raises(ValueError, match="ghost"):
        export_glb(tmp_path / "ghost.glb", spec, plan(spec), [clip])


def test_mixed_missing_translation_keyframes_are_rejected(tmp_path: Path) -> None:
    spec = make_spec()
    clip = BakedClip(
        clip_id="bad",
        tracks=[
            BakedTrack(
                part_id="arm",
                keyframes=[
                    TRSKeyframe(t=0.0, translation=(0.0, 0.0, 0.0)),
                    TRSKeyframe(t=1.0, translation=None),
                ],
            )
        ],
    )
    with pytest.raises(ValueError, match="translation"):
        export_glb(tmp_path / "mixed.glb", spec, plan(spec), [clip])


def test_antenna_end_to_end_bake_and_export(
    tmp_path: Path, antenna_spec_dict: dict[str, Any]
) -> None:
    spec = validate_spec(normalize_spec(MotionSpec.model_validate(antenna_spec_dict)))
    graph = plan(spec)
    baked = bake(spec, graph)
    out = export_glb(tmp_path / "antenna.glb", spec, graph, baked)
    doc, binary = _read_glb(out)
    assert [a["name"] for a in doc["animations"]] == ["scan_loop", "maintenance_open"]
    scan = doc["animations"][0]
    # scan_loop drives mast (node 2) and dish (node 4).
    assert {c["target"]["node"] for c in scan["channels"]} == {2, 4}
    hatch_channels = _channel_outputs(doc, binary, doc["animations"][1])
    assert hatch_channels["rotation"]["input"][-1] == pytest.approx(1.2)
    half = math.radians(95.0) / 2
    assert hatch_channels["rotation"]["output"][-1] == pytest.approx(
        (0.0, math.sin(half), 0.0, math.cos(half))
    )
