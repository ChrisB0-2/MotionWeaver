"""The part graph: movable parts and their candidate parent/child relationships.

The part graph is an intermediate, geometry-derived structure. It is *distinct*
from the runtime kinematic graph: it captures spatial adjacency and containment
hints, while the kinematic graph (see :mod:`mw_core.rig.kinematic_graph`) encodes
validated joints. The dependency-free pieces here are implemented so they can be
unit-tested without ``trimesh``/``Open3D`` installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Part:
    """A candidate movable part discovered from geometry."""

    id: str
    object_names: list[str] = field(default_factory=list)
    # Index into the source mesh's connected components, if known.
    connected_component_ids: list[int] = field(default_factory=list)


@dataclass
class PartGraph:
    """An undirected adjacency graph over candidate parts.

    Adjacency means "these parts touch / are spatially coupled" and is a *hint*
    for joint parent/child assignment, not a validated kinematic relationship.
    """

    parts: dict[str, Part] = field(default_factory=dict)
    _adjacency: dict[str, set[str]] = field(default_factory=dict)

    def add_part(self, part: Part) -> None:
        if part.id in self.parts:
            raise ValueError(f"duplicate part id: {part.id!r}")
        self.parts[part.id] = part
        self._adjacency.setdefault(part.id, set())

    def add_adjacency(self, a: str, b: str) -> None:
        if a not in self.parts or b not in self.parts:
            raise KeyError("both parts must be added before linking them")
        if a == b:
            raise ValueError("a part cannot be adjacent to itself")
        self._adjacency[a].add(b)
        self._adjacency[b].add(a)

    def neighbors(self, part_id: str) -> set[str]:
        return set(self._adjacency[part_id])

    def connected_components(self) -> list[set[str]]:
        """Return connected components of the adjacency graph."""
        seen: set[str] = set()
        components: list[set[str]] = []
        for start in self.parts:
            if start in seen:
                continue
            stack = [start]
            comp: set[str] = set()
            while stack:
                node = stack.pop()
                if node in seen:
                    continue
                seen.add(node)
                comp.add(node)
                stack.extend(self._adjacency[node] - seen)
            components.append(comp)
        return components


def split_connected_components(mesh: object) -> list[Part]:
    """Split a mesh into rigid candidate parts by connected geometry.

    TODO: implement with ``trimesh``'s ``mesh.split(only_watertight=False)`` and
    Blender loose-part separation. Welded single meshes should return a single
    part and surface an uncertainty flag for human confirmation rather than
    guessing boundaries.
    """
    raise NotImplementedError("connected-component splitting not implemented yet")
