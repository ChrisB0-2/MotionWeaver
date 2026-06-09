"""Compile a validated ``motion_spec`` into a :class:`KinematicGraph`.

The planner assumes the spec has already passed semantic validation (acyclic,
references resolve). It assembles the parent/child tree from the joints.
"""

from __future__ import annotations

from mw_core.motion_spec.models import MotionSpec
from mw_core.rig.kinematic_graph import KinematicGraph, KinematicNode


def plan(spec: MotionSpec) -> KinematicGraph:
    """Build the kinematic graph from a validated spec.

    TODO: handle yaw_pitch joints that expand into a two-axis stack, and parts
    that participate in multiple joints. For now this builds the basic tree from
    single parent->child joints.
    """
    nodes: dict[str, KinematicNode] = {p.id: KinematicNode(part_id=p.id) for p in spec.parts}
    has_parent: set[str] = set()

    for joint in spec.joints:
        parent = nodes[joint.parent_part]
        child = nodes[joint.child_part]
        child.joint = joint
        parent.children.append(child)
        has_parent.add(joint.child_part)

    roots = [node for pid, node in nodes.items() if pid not in has_parent]
    return KinematicGraph(roots=roots)
