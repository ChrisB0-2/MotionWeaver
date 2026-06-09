"""The rig-agnostic kinematic graph.

A directed tree of parts connected by joints. Each node carries the joint that
attaches it to its parent (the root has none). This structure is what backends
compile against; it lives entirely outside Blender.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mw_core.motion_spec.models import Joint


@dataclass
class KinematicNode:
    part_id: str
    # The joint attaching this node to its parent; None for the root.
    joint: Joint | None = None
    children: list[KinematicNode] = field(default_factory=list)


@dataclass
class KinematicGraph:
    roots: list[KinematicNode] = field(default_factory=list)

    def iter_nodes(self) -> list[KinematicNode]:
        """Pre-order traversal of all nodes."""
        out: list[KinematicNode] = []
        stack = list(reversed(self.roots))
        while stack:
            node = stack.pop()
            out.append(node)
            stack.extend(reversed(node.children))
        return out
