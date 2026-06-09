"""The rig-agnostic kinematic graph and the planner/baker that produce it.

The kinematic graph is MotionWeaver's canonical runtime representation. Backends
(Blender, glTF, Unity) are compiled *from* it; it is never derived from a
backend.
"""

from __future__ import annotations

from mw_core.rig.kinematic_graph import KinematicGraph, KinematicNode

__all__ = ["KinematicGraph", "KinematicNode"]
