"""Baking clips into parent-relative TRS keyframe tracks."""

from __future__ import annotations

import math
from typing import Any

import pytest

from mw_core import MotionSpec, normalize_spec, validate_spec
from mw_core.rig.baker import bake
from mw_core.rig.planner import plan

Keyframes = list[tuple[float, float] | tuple[float, float, str]]


def make_spec(
    *,
    joint_type: str = "hinge",
    axis: list[float] | None = None,
    pivot: list[float] | None = None,
    pivot_space: str = "world",
    control_property: str = "angle_deg",
    keyframes: Keyframes | None = None,
    duration_s: float | None = 1.0,
    controls: list[dict[str, Any]] | None = None,
    channels: list[dict[str, Any]] | None = None,
) -> MotionSpec:
    """Build a minimal validated two-part spec: base --j1--> arm, control c1, clip clip1."""
    if keyframes is None:
        keyframes = [(0.0, 0.0), (1.0, 90.0)]
    keyframe_dicts = [
        {"t": kf[0], "value": kf[1], "interp": kf[2] if len(kf) == 3 else "linear"}
        for kf in keyframes
    ]
    if controls is None:
        controls = [
            {"id": "c1", "label": "Control 1", "joint_id": "j1", "property": control_property}
        ]
    if channels is None:
        channels = [{"control_id": "c1", "keyframes": keyframe_dicts}]
    payload = {
        "schema_version": "0.1.0",
        "asset_id": "baker_test",
        "coordinate_system": {"up_axis": "Z", "forward_axis": "Y", "unit_scale_meters": 1.0},
        "parts": [
            {"id": "base", "name": "Base", "selector": {"object_names": ["Base"]}},
            {"id": "arm", "name": "Arm", "selector": {"object_names": ["Arm"]}},
        ],
        "joints": [
            {
                "id": "j1",
                "type": joint_type,
                "parent_part": "base",
                "child_part": "arm",
                "pivot": {"space": pivot_space, "position": pivot or [0.0, 0.0, 0.0]},
                "axis": axis or [0.0, 0.0, 1.0],
            }
        ],
        "controls": controls,
        "clips": [
            {"id": "clip1", "name": "Clip 1", "duration_s": duration_s, "channels": channels}
        ],
    }
    return validate_spec(MotionSpec.model_validate(payload))


def _only_track_keyframes(spec: MotionSpec, **bake_kwargs: Any) -> list[Any]:
    (clip,) = bake(spec, plan(spec), **bake_kwargs)
    (track,) = clip.tracks
    return track.keyframes


def test_hinge_bakes_rotation_and_pivot_offset_translation() -> None:
    spec = make_spec(
        axis=[0.0, 0.0, 1.0], pivot=[1.0, 0.0, 0.0], keyframes=[(0.0, 0.0), (1.0, 90.0)]
    )
    (clip,) = bake(spec, plan(spec), sample_rate_hz=1.0)
    assert clip.clip_id == "clip1"
    (track,) = clip.tracks
    assert track.part_id == "arm"
    first, last = track.keyframes[0], track.keyframes[-1]
    assert first.t == 0.0
    assert first.rotation_quat == pytest.approx((0.0, 0.0, 0.0, 1.0))
    assert first.translation == pytest.approx((0.0, 0.0, 0.0))
    # 90 deg about Z through pivot (1,0,0): quat is XYZW, translation = p - R*p.
    half = math.radians(90.0) / 2
    assert last.t == pytest.approx(1.0)
    assert last.rotation_quat == pytest.approx((0.0, 0.0, math.sin(half), math.cos(half)))
    assert last.translation == pytest.approx((1.0, -1.0, 0.0))
    assert last.scale is None


def test_spin_bakes_like_hinge() -> None:
    spec = make_spec(joint_type="spin", axis=[0.0, 1.0, 0.0], keyframes=[(0.0, 0.0), (1.0, 180.0)])
    keyframes = _only_track_keyframes(spec, sample_rate_hz=1.0)
    assert keyframes[-1].rotation_quat == pytest.approx((0.0, 1.0, 0.0, 0.0), abs=1e-12)


def test_slider_translates_along_normalized_axis() -> None:
    spec = make_spec(
        joint_type="slider",
        axis=[0.0, 0.0, 2.0],
        control_property="distance_m",
        keyframes=[(0.0, 0.0), (1.0, 0.5)],
    )
    keyframes = _only_track_keyframes(spec, sample_rate_hz=1.0)
    assert keyframes[-1].translation == pytest.approx((0.0, 0.0, 0.5))
    assert keyframes[-1].rotation_quat is None


def test_sample_times_are_uniform_and_end_exactly_at_duration() -> None:
    spec = make_spec(keyframes=[(0.0, 0.0), (1.0, 90.0)], duration_s=1.0)
    times = [kf.t for kf in _only_track_keyframes(spec, sample_rate_hz=4.0)]
    assert times == pytest.approx([0.0, 0.25, 0.5, 0.75, 1.0])

    spec = make_spec(keyframes=[(0.0, 0.0), (0.3, 90.0)], duration_s=0.3)
    times = [kf.t for kf in _only_track_keyframes(spec, sample_rate_hz=4.0)]
    assert times == pytest.approx([0.0, 0.25, 0.3])


def test_linear_interpolation_between_keyframes() -> None:
    spec = make_spec(
        joint_type="slider",
        axis=[0.0, 0.0, 1.0],
        control_property="distance_m",
        keyframes=[(0.0, 0.0), (2.0, 1.0)],
        duration_s=2.0,
    )
    z_values = [kf.translation[2] for kf in _only_track_keyframes(spec, sample_rate_hz=1.0)]
    assert z_values == pytest.approx([0.0, 0.5, 1.0])


def test_step_interpolation_holds_until_next_keyframe() -> None:
    spec = make_spec(
        joint_type="slider",
        axis=[0.0, 0.0, 1.0],
        control_property="distance_m",
        keyframes=[(0.0, 0.0, "step"), (1.0, 1.0)],
    )
    z_values = [kf.translation[2] for kf in _only_track_keyframes(spec, sample_rate_hz=2.0)]
    assert z_values == pytest.approx([0.0, 0.0, 1.0])


def test_value_is_held_outside_the_keyframe_range() -> None:
    spec = make_spec(
        joint_type="slider",
        axis=[0.0, 0.0, 1.0],
        control_property="distance_m",
        keyframes=[(0.5, 2.0)],
    )
    z_values = [kf.translation[2] for kf in _only_track_keyframes(spec, sample_rate_hz=2.0)]
    assert z_values == pytest.approx([2.0, 2.0, 2.0])


def test_duration_defaults_to_last_keyframe_time() -> None:
    spec = make_spec(keyframes=[(0.0, 0.0), (2.0, 90.0)], duration_s=None)
    times = [kf.t for kf in _only_track_keyframes(spec, sample_rate_hz=1.0)]
    assert times == pytest.approx([0.0, 1.0, 2.0])


def test_yaw_pitch_joints_are_rejected_for_now() -> None:
    spec = make_spec(joint_type="yaw_pitch")
    with pytest.raises(NotImplementedError, match="yaw_pitch"):
        bake(spec, plan(spec))


def test_cubic_interpolation_is_rejected_for_now() -> None:
    spec = make_spec(keyframes=[(0.0, 0.0, "cubic"), (1.0, 90.0)])
    with pytest.raises(NotImplementedError, match="cubic"):
        bake(spec, plan(spec))


def test_bbox_normalized_pivot_space_is_rejected_for_now() -> None:
    spec = make_spec(pivot_space="part_bbox_normalized")
    with pytest.raises(NotImplementedError, match="part_bbox_normalized"):
        bake(spec, plan(spec))


def test_multiple_channels_driving_one_joint_raise() -> None:
    keyframe_dicts = [{"t": 0.0, "value": 0.0}, {"t": 1.0, "value": 90.0}]
    spec = make_spec(
        controls=[
            {"id": "c1", "label": "Control 1", "joint_id": "j1", "property": "angle_deg"},
            {"id": "c2", "label": "Control 2", "joint_id": "j1", "property": "angle_deg"},
        ],
        channels=[
            {"control_id": "c1", "keyframes": keyframe_dicts},
            {"control_id": "c2", "keyframes": keyframe_dicts},
        ],
    )
    with pytest.raises(ValueError, match="j1"):
        bake(spec, plan(spec))


def test_channel_without_keyframes_produces_no_track() -> None:
    spec = make_spec(channels=[{"control_id": "c1", "keyframes": []}])
    (clip,) = bake(spec, plan(spec))
    assert clip.tracks == []


def test_antenna_example_bakes_every_clip(antenna_spec_dict: dict[str, Any]) -> None:
    spec = validate_spec(normalize_spec(MotionSpec.model_validate(antenna_spec_dict)))
    clips = bake(spec, plan(spec))
    assert [c.clip_id for c in clips] == ["scan_loop", "maintenance_open"]
    scan, maintenance = clips
    assert {t.part_id for t in scan.tracks} == {"mast", "dish"}
    assert {t.part_id for t in maintenance.tracks} == {"service_hatch"}
    for track in scan.tracks:
        assert track.keyframes[0].t == 0.0
        assert track.keyframes[-1].t == pytest.approx(6.0)
    (hatch,) = maintenance.tracks
    last = hatch.keyframes[-1]
    assert last.t == pytest.approx(1.2)
    # Hatch ends fully open: 95 deg about +Y.
    half = math.radians(95.0) / 2
    assert last.rotation_quat == pytest.approx((0.0, math.sin(half), 0.0, math.cos(half)))
