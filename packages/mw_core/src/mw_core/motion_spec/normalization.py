"""Deterministic normalization of a ``motion_spec`` before validation/compilation.

Normalization is *lossless-where-safe* cleanup that callers can rely on:
joint axis vectors are unit-length, and yaw_pitch stacks default sensibly. It
does not invent geometry or resolve ambiguity; that is the human's job.
"""

from __future__ import annotations

import math

from mw_core.motion_spec.models import JointType, MotionSpec, Vec3

# Axes shorter than this are treated as degenerate (cannot be normalized).
_MIN_AXIS_NORM = 1e-9


def _vec_norm(v: Vec3) -> float:
    return math.sqrt(sum(c * c for c in v))


def normalize_axis(axis: Vec3) -> Vec3:
    """Return a unit-length copy of ``axis``.

    Raises ``ValueError`` if the axis is degenerate (near-zero length).
    """
    n = _vec_norm(axis)
    if n < _MIN_AXIS_NORM:
        raise ValueError(f"degenerate axis vector cannot be normalized: {axis!r}")
    return [c / n for c in axis]


def normalize_spec(spec: MotionSpec) -> MotionSpec:
    """Return a normalized deep copy of ``spec``.

    - Joint axis vectors are normalized to unit length.
    - ``yaw_pitch`` joints without an explicit stack default to ``["yaw", "pitch"]``.
    """
    out = spec.model_copy(deep=True)
    for joint in out.joints:
        joint.axis = normalize_axis(joint.axis)
        if joint.type is JointType.YAW_PITCH and not joint.stack:
            joint.stack = ["yaw", "pitch"]
    return out
