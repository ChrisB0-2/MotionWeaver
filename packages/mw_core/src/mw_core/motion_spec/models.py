"""Pydantic models for the ``motion_spec`` schema.

These mirror ``schemas/motion_spec.schema.json``. The models enforce *syntactic*
constraints (types, enums, vector arity, ranges). Cross-reference and geometric
*semantic* constraints live in :mod:`mw_core.motion_spec.semantic_validation`.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class _Model(BaseModel):
    """Base model: reject unknown fields, matching ``additionalProperties: false``."""

    model_config = ConfigDict(extra="forbid")


# Six signed cardinal axes, e.g. "Z" or "-Y".
Axis6 = str

# A 3-component vector.
Vec3 = list[float]


class JointType(StrEnum):
    """The fixed, testable joint vocabulary. Do not extend without a schema bump."""

    HINGE = "hinge"
    SLIDER = "slider"
    SPIN = "spin"
    YAW_PITCH = "yaw_pitch"


class PivotSpace(StrEnum):
    LOCAL = "local"
    WORLD = "world"
    PART_BBOX_NORMALIZED = "part_bbox_normalized"


class ControlProperty(StrEnum):
    ANGLE_DEG = "angle_deg"
    DISTANCE_M = "distance_m"


class Interp(StrEnum):
    STEP = "step"
    LINEAR = "linear"
    CUBIC = "cubic"


class SourceMesh(_Model):
    file_name: str | None = None
    units: str | None = None
    notes: str | None = None


class CoordinateSystem(_Model):
    up_axis: Axis6
    forward_axis: Axis6
    unit_scale_meters: float = Field(gt=0.0)


class Selector(_Model):
    """How a part maps onto imported geometry. At least one strategy should resolve."""

    object_names: list[str] = Field(default_factory=list)
    material_names: list[str] = Field(default_factory=list)
    connected_component_ids: list[int] = Field(default_factory=list)


class Part(_Model):
    id: str
    name: str
    selector: Selector
    is_static: bool = False


class Pivot(_Model):
    space: PivotSpace
    position: Vec3 = Field(min_length=3, max_length=3)


class Limits(_Model):
    min_deg: float | None = None
    max_deg: float | None = None
    min_m: float | None = None
    max_m: float | None = None


class Joint(_Model):
    id: str
    type: JointType
    parent_part: str
    child_part: str
    pivot: Pivot
    axis: Vec3 = Field(min_length=3, max_length=3)
    limits: Limits | None = None
    # Ordered stack for yaw_pitch joints, e.g. ["yaw", "pitch"].
    stack: list[str] | None = None
    notes: str | None = None


class Control(_Model):
    id: str
    label: str
    joint_id: str
    property: ControlProperty
    default: float | None = None
    ui_min: float | None = None
    ui_max: float | None = None


class Keyframe(_Model):
    t: float = Field(ge=0.0)
    value: float
    interp: Interp = Interp.LINEAR


class Channel(_Model):
    control_id: str
    keyframes: list[Keyframe]


class Clip(_Model):
    id: str
    name: str
    duration_s: float | None = Field(default=None, gt=0.0)
    loop: bool = False
    channels: list[Channel]


class MotionSpec(_Model):
    """Top-level backend-agnostic motion contract."""

    schema_version: str
    asset_id: str
    coordinate_system: CoordinateSystem
    parts: list[Part]
    joints: list[Joint]
    controls: list[Control]
    clips: list[Clip]
    source_mesh: SourceMesh | None = None
    assumptions: list[str] = Field(default_factory=list)
