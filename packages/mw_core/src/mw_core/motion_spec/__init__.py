"""The canonical, backend-agnostic ``motion_spec`` data model and validation.

A ``motion_spec`` describes **parts, joints, controls, clips, and assumptions**.
It never contains Blender or engine code. It is the single source of truth that
the deterministic compiler consumes.
"""

from __future__ import annotations

from mw_core.motion_spec.models import (
    Axis6,
    Clip,
    Control,
    ControlProperty,
    CoordinateSystem,
    Joint,
    JointType,
    Keyframe,
    Limits,
    MotionSpec,
    Part,
    PivotSpace,
)
from mw_core.motion_spec.normalization import normalize_spec
from mw_core.motion_spec.semantic_validation import (
    SemanticError,
    semantic_issues,
    validate_spec,
)

__all__ = [
    "Axis6",
    "Clip",
    "Control",
    "ControlProperty",
    "CoordinateSystem",
    "Joint",
    "JointType",
    "Keyframe",
    "Limits",
    "MotionSpec",
    "Part",
    "PivotSpace",
    "SemanticError",
    "normalize_spec",
    "semantic_issues",
    "validate_spec",
]
