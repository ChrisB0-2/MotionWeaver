"""Bake control-driven clips into per-node TRS keyframe tracks.

glTF's portable animation model is node translation/rotation/scale tracks, so
every exportable clip must be baked from high-level control values into TRS
samples on the affected kinematic nodes. Blender drivers/constraints are
preview-only and must not survive into the baked output.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mw_core.motion_spec.models import MotionSpec
from mw_core.rig.kinematic_graph import KinematicGraph


@dataclass
class TRSKeyframe:
    t: float
    translation: tuple[float, float, float] | None = None
    rotation_quat: tuple[float, float, float, float] | None = None
    scale: tuple[float, float, float] | None = None


@dataclass
class BakedTrack:
    part_id: str
    keyframes: list[TRSKeyframe] = field(default_factory=list)


@dataclass
class BakedClip:
    clip_id: str
    tracks: list[BakedTrack] = field(default_factory=list)


def bake(spec: MotionSpec, graph: KinematicGraph) -> list[BakedClip]:
    """Bake all clips in ``spec`` into TRS tracks against ``graph``.

    TODO: for each clip channel, resolve control -> joint -> node, sample control
    values at the requested rate (respecting interp), and compose joint transforms
    down the kinematic chain into world/local TRS keyframes ready for glTF export.
    """
    raise NotImplementedError("clip baking not implemented yet")
