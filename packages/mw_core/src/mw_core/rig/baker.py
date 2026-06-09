"""Bake control-driven clips into per-node TRS keyframe tracks.

glTF's portable animation model is node translation/rotation/scale tracks, so
every exportable clip must be baked from high-level control values into TRS
samples on the affected kinematic nodes. Blender drivers/constraints are
preview-only and must not survive into the baked output.

Baked keyframes are the child part node's transform *relative to its parent
part node*, assuming identity rest transforms (geometry authored in the shared
world frame, as the importers produce). The scene-graph hierarchy then composes
motion down the chain, so tracks need no per-chain math. Quaternions use glTF
XYZW component order.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from mw_core.motion_spec.models import (
    Interp,
    Joint,
    JointType,
    Keyframe,
    MotionSpec,
    PivotSpace,
)
from mw_core.motion_spec.normalization import normalize_axis
from mw_core.rig.kinematic_graph import KinematicGraph

_EPS = 1e-9

Vec3 = tuple[float, float, float]
QuatXYZW = tuple[float, float, float, float]


@dataclass
class TRSKeyframe:
    t: float
    translation: Vec3 | None = None
    rotation_quat: QuatXYZW | None = None
    scale: Vec3 | None = None


@dataclass
class BakedTrack:
    part_id: str
    keyframes: list[TRSKeyframe] = field(default_factory=list)


@dataclass
class BakedClip:
    clip_id: str
    tracks: list[BakedTrack] = field(default_factory=list)


def _sample_times(duration: float, rate: float) -> list[float]:
    """Uniform sample times at ``rate`` Hz covering [0, duration], endpoint included."""
    count = int(math.floor(duration * rate + _EPS))
    times = [i / rate for i in range(count + 1)]
    if duration - times[-1] > _EPS:
        times.append(duration)
    return times


def _evaluate(keyframes: list[Keyframe], t: float) -> float:
    """Evaluate a channel at ``t``; values hold flat outside the keyframe range.

    A keyframe's ``interp`` describes the segment leaving it (toward the next
    keyframe), matching Blender's convention.
    """
    if t <= keyframes[0].t:
        return keyframes[0].value
    if t >= keyframes[-1].t:
        return keyframes[-1].value
    for a, b in zip(keyframes, keyframes[1:], strict=False):
        if a.t <= t < b.t:
            if a.interp is Interp.STEP:
                return a.value
            dt = b.t - a.t
            if dt <= _EPS:
                return b.value
            return a.value + (b.value - a.value) * (t - a.t) / dt
    return keyframes[-1].value


def _axis_angle_quat(axis: list[float], angle_deg: float) -> QuatXYZW:
    half = math.radians(angle_deg) / 2.0
    s = math.sin(half)
    return (axis[0] * s, axis[1] * s, axis[2] * s, math.cos(half))


def _rotate_vec(q: QuatXYZW, v: Vec3) -> Vec3:
    """Rotate ``v`` by unit quaternion ``q``: v' = v + w*t + u x t, t = 2(u x v)."""
    x, y, z, w = q
    tx = 2.0 * (y * v[2] - z * v[1])
    ty = 2.0 * (z * v[0] - x * v[2])
    tz = 2.0 * (x * v[1] - y * v[0])
    return (
        v[0] + w * tx + (y * tz - z * ty),
        v[1] + w * ty + (z * tx - x * tz),
        v[2] + w * tz + (x * ty - y * tx),
    )


def _joint_keyframe(joint: Joint, axis: list[float], value: float, t: float) -> TRSKeyframe:
    if joint.type in (JointType.HINGE, JointType.SPIN):
        quat = _axis_angle_quat(axis, value)
        p = joint.pivot.position
        rotated = _rotate_vec(quat, (p[0], p[1], p[2]))
        translation = (p[0] - rotated[0], p[1] - rotated[1], p[2] - rotated[2])
        return TRSKeyframe(t=t, translation=translation, rotation_quat=quat)
    if joint.type is JointType.SLIDER:
        return TRSKeyframe(t=t, translation=(axis[0] * value, axis[1] * value, axis[2] * value))
    raise NotImplementedError(f"baking is not implemented for {joint.type.value} joints yet")


def bake(
    spec: MotionSpec, graph: KinematicGraph, *, sample_rate_hz: float = 30.0
) -> list[BakedClip]:
    """Bake all clips in ``spec`` into parent-relative TRS tracks against ``graph``.

    Each clip channel resolves control -> joint -> graph node; control values are
    sampled uniformly at ``sample_rate_hz`` (endpoint included) and turned into
    one TRS keyframe per sample on the joint's child part node. Only parts driven
    by a channel get a track; undriven parts stay at rest.
    """
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    controls_by_id = {c.id: c for c in spec.controls}
    joints_by_id = {j.id: j for j in spec.joints}
    part_by_joint_id = {
        node.joint.id: node.part_id for node in graph.iter_nodes() if node.joint is not None
    }

    baked: list[BakedClip] = []
    for clip in spec.clips:
        duration = clip.duration_s
        if duration is None:
            duration = max((kf.t for ch in clip.channels for kf in ch.keyframes), default=0.0)
        times = _sample_times(duration, sample_rate_hz)

        tracks: list[BakedTrack] = []
        driven_joints: set[str] = set()
        for channel in clip.channels:
            if not channel.keyframes:
                continue
            control = controls_by_id[channel.control_id]
            joint = joints_by_id[control.joint_id]
            if joint.id in driven_joints:
                raise ValueError(f"clip {clip.id!r}: multiple channels drive joint {joint.id!r}")
            driven_joints.add(joint.id)
            if joint.type is JointType.YAW_PITCH:
                raise NotImplementedError(
                    f"joint {joint.id!r}: yaw_pitch joints are not supported by the baker "
                    "until the planner expands their two-axis stack"
                )
            if joint.pivot.space is PivotSpace.PART_BBOX_NORMALIZED:
                raise NotImplementedError(
                    f"joint {joint.id!r}: part_bbox_normalized pivots need geometry context "
                    "the baker does not have yet"
                )
            if any(kf.interp is Interp.CUBIC for kf in channel.keyframes):
                raise NotImplementedError(
                    f"clip {clip.id!r} channel {channel.control_id!r}: cubic keyframe "
                    "interpolation is not supported by the baker yet"
                )
            if joint.id not in part_by_joint_id:
                raise ValueError(f"joint {joint.id!r} is not present in the kinematic graph")
            axis = normalize_axis(joint.axis)
            track = BakedTrack(part_id=part_by_joint_id[joint.id])
            for t in times:
                value = _evaluate(channel.keyframes, t)
                track.keyframes.append(_joint_keyframe(joint, axis, value, t))
            tracks.append(track)
        baked.append(BakedClip(clip_id=clip.id, tracks=tracks))
    return baked
