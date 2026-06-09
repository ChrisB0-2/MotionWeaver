"""Semantic validation of a ``motion_spec``.

Pydantic guarantees the spec is *syntactically* well-formed. These checks
guarantee it is *semantically coherent* before the deterministic compiler builds
anything:

- part ids are unique;
- joint ``parent_part`` / ``child_part`` references resolve to real parts;
- the parent→child joint graph is acyclic (no kinematic cycles);
- joint axis vectors are non-degenerate (unit-length after normalization);
- joint limits are sane for the joint type (e.g. hinge uses degrees, min <= max);
- controls reference existing joints with a property the joint supports;
- clip channels reference existing controls and have ordered keyframes.

This is the highest-leverage reliability layer: it turns AI output into an input
*language* rather than executable truth.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

from mw_core.motion_spec.models import (
    ControlProperty,
    Joint,
    JointType,
    MotionSpec,
)

_MIN_AXIS_NORM = 1e-9

# Joint types whose controllable quantity is an angle (degrees) vs a distance.
_ANGULAR_JOINTS = {JointType.HINGE, JointType.SPIN, JointType.YAW_PITCH}
_LINEAR_JOINTS = {JointType.SLIDER}


class SemanticError(ValueError):
    """Raised by :func:`validate_spec` when one or more semantic issues are found."""

    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        super().__init__(
            f"motion_spec failed semantic validation ({len(issues)} issue(s)):\n"
            + "\n".join(f"  - {i}" for i in issues)
        )


def _axis_degenerate(axis: Iterable[float]) -> bool:
    return math.sqrt(sum(c * c for c in axis)) < _MIN_AXIS_NORM


def _check_part_ids(spec: MotionSpec) -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for part in spec.parts:
        if part.id in seen:
            issues.append(f"duplicate part id: {part.id!r}")
        seen.add(part.id)
    return issues


def _check_joint_refs(spec: MotionSpec, part_ids: set[str]) -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for joint in spec.joints:
        if joint.id in seen:
            issues.append(f"duplicate joint id: {joint.id!r}")
        seen.add(joint.id)
        if joint.parent_part not in part_ids:
            issues.append(
                f"joint {joint.id!r} references unknown parent_part {joint.parent_part!r}"
            )
        if joint.child_part not in part_ids:
            issues.append(f"joint {joint.id!r} references unknown child_part {joint.child_part!r}")
        if joint.parent_part == joint.child_part:
            issues.append(f"joint {joint.id!r} connects part {joint.parent_part!r} to itself")
        if _axis_degenerate(joint.axis):
            issues.append(f"joint {joint.id!r} has a degenerate (zero-length) axis")
        issues.extend(_check_limits(joint))
    return issues


def _check_limits(joint: Joint) -> list[str]:
    issues: list[str] = []
    lim = joint.limits
    if lim is None:
        return issues
    if joint.type in _ANGULAR_JOINTS:
        if lim.min_m is not None or lim.max_m is not None:
            issues.append(
                f"joint {joint.id!r} ({joint.type.value}) uses linear limits (min_m/max_m)"
            )
        if lim.min_deg is not None and lim.max_deg is not None and lim.min_deg > lim.max_deg:
            issues.append(f"joint {joint.id!r} has min_deg > max_deg")
    if joint.type in _LINEAR_JOINTS:
        if lim.min_deg is not None or lim.max_deg is not None:
            issues.append(f"joint {joint.id!r} (slider) uses angular limits (min_deg/max_deg)")
        if lim.min_m is not None and lim.max_m is not None and lim.min_m > lim.max_m:
            issues.append(f"joint {joint.id!r} has min_m > max_m")
    return issues


def _check_acyclic(spec: MotionSpec) -> list[str]:
    """Detect cycles in the parent_part -> child_part directed graph."""
    children: dict[str, list[str]] = {}
    for joint in spec.joints:
        children.setdefault(joint.parent_part, []).append(joint.child_part)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {}

    def visit(node: str, path: list[str]) -> list[str] | None:
        color[node] = GRAY
        for nxt in children.get(node, []):
            c = color.get(nxt, WHITE)
            if c == GRAY:
                cycle = path + [node, nxt]
                return cycle
            if c == WHITE:
                found = visit(nxt, path + [node])
                if found is not None:
                    return found
        color[node] = BLACK
        return None

    for node in list(children.keys()):
        if color.get(node, WHITE) == WHITE:
            cycle = visit(node, [])
            if cycle is not None:
                return [f"kinematic cycle detected: {' -> '.join(cycle)}"]
    return []


def _check_controls(spec: MotionSpec, joints_by_id: dict[str, Joint]) -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for control in spec.controls:
        if control.id in seen:
            issues.append(f"duplicate control id: {control.id!r}")
        seen.add(control.id)
        joint = joints_by_id.get(control.joint_id)
        if joint is None:
            issues.append(f"control {control.id!r} references unknown joint {control.joint_id!r}")
            continue
        if control.property is ControlProperty.ANGLE_DEG and joint.type not in _ANGULAR_JOINTS:
            issues.append(
                f"control {control.id!r} drives angle_deg but joint {joint.id!r} "
                f"is {joint.type.value}"
            )
        if control.property is ControlProperty.DISTANCE_M and joint.type not in _LINEAR_JOINTS:
            issues.append(
                f"control {control.id!r} drives distance_m but joint {joint.id!r} "
                f"is {joint.type.value}"
            )
        if (
            control.ui_min is not None
            and control.ui_max is not None
            and control.ui_min > control.ui_max
        ):
            issues.append(f"control {control.id!r} has ui_min > ui_max")
    return issues


def _check_clips(spec: MotionSpec, control_ids: set[str]) -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for clip in spec.clips:
        if clip.id in seen:
            issues.append(f"duplicate clip id: {clip.id!r}")
        seen.add(clip.id)
        for ci, channel in enumerate(clip.channels):
            if channel.control_id not in control_ids:
                issues.append(
                    f"clip {clip.id!r} channel {ci} references unknown control "
                    f"{channel.control_id!r}"
                )
            times = [kf.t for kf in channel.keyframes]
            if times != sorted(times):
                issues.append(
                    f"clip {clip.id!r} channel {ci} ({channel.control_id!r}) "
                    "has out-of-order keyframe times"
                )
            if clip.duration_s is not None and times and max(times) > clip.duration_s:
                issues.append(f"clip {clip.id!r} channel {ci} has a keyframe past duration_s")
    return issues


def semantic_issues(spec: MotionSpec) -> list[str]:
    """Return a list of human-readable semantic issues (empty if the spec is valid)."""
    part_ids = {p.id for p in spec.parts}
    joints_by_id = {j.id: j for j in spec.joints}
    control_ids = {c.id for c in spec.controls}

    issues: list[str] = []
    issues += _check_part_ids(spec)
    issues += _check_joint_refs(spec, part_ids)
    issues += _check_acyclic(spec)
    issues += _check_controls(spec, joints_by_id)
    issues += _check_clips(spec, control_ids)
    return issues


def validate_spec(spec: MotionSpec) -> MotionSpec:
    """Validate ``spec`` semantically, raising :class:`SemanticError` on failure.

    Returns the spec unchanged on success so it can be used inline.
    """
    issues = semantic_issues(spec)
    if issues:
        raise SemanticError(issues)
    return spec
