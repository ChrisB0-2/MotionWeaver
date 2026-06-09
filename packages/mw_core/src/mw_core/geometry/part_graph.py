"""The part graph: movable parts and their candidate parent/child relationships.

The part graph is an intermediate, geometry-derived structure. It is *distinct*
from the runtime kinematic graph: it captures spatial adjacency and containment
hints, while the kinematic graph (see :mod:`mw_core.rig.kinematic_graph`) encodes
validated joints. The dependency-free pieces here are implemented so they can be
unit-tested without ``trimesh``/``Open3D`` installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # trimesh is an optional ("geometry" extra) dependency; this import exists
    # only so annotations read clearly. (Runtime code below stays duck-typed
    # because trimesh's own annotations collapse meshes to a loose Geometry
    # base type, not because stubs are missing — trimesh ships py.typed.)
    import trimesh


@dataclass
class Part:
    """A candidate movable part discovered from geometry."""

    id: str
    object_names: list[str] = field(default_factory=list)
    # Index into the source mesh's connected components, if known.
    connected_component_ids: list[int] = field(default_factory=list)
    # Triangle count of the source geometry (0 if unknown).
    face_count: int = 0
    # True when this part needs human confirmation before it can be trusted as a
    # rigid boundary (e.g. a welded single mesh with no separable components).
    is_uncertain: bool = False


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


def split_connected_components(
    mesh: trimesh.Trimesh | trimesh.Scene,
    *,
    id_prefix: str = "part",
    min_faces: int = 1,
) -> list[Part]:
    """Split a mesh into rigid candidate parts by connected geometry.

    Uses trimesh connected-component splitting
    (``mesh.split(only_watertight=False)``) so physically disconnected sub-meshes
    become separate candidate parts. A ``trimesh.Scene`` is first concatenated
    into a single mesh (``scene.to_geometry()``, or ``dump`` on older trimesh).

    Each returned :class:`Part` records its source component index in
    ``connected_component_ids`` and its triangle count in ``face_count``. Parts
    are ordered by descending triangle count so the largest (typically the body)
    comes first, and ids are assigned sequentially (``{id_prefix}_000`` ...).

    A *welded* mesh that yields a single component is returned as one part with
    ``is_uncertain=True``: connected-component analysis cannot recover rigid
    boundaries inside welded geometry, so a human (or a vision-assist pass) must
    confirm or manually separate it rather than the tool guessing.

    Args:
        mesh: a ``trimesh.Trimesh`` or ``trimesh.Scene``.
        id_prefix: prefix for generated part ids.
        min_faces: components with fewer triangles are discarded as noise.
            Set to ``0`` to keep every component.

    Raises:
        TypeError: if ``mesh`` is not a trimesh ``Trimesh``/``Scene``.
    """
    components = _split_mesh(mesh)

    # (original_component_index, face_count), filtered then sorted largest-first.
    indexed = [(idx, int(len(comp.faces))) for idx, comp in enumerate(components)]
    if min_faces > 0:
        indexed = [(idx, fc) for idx, fc in indexed if fc >= min_faces]
    indexed.sort(key=lambda pair: pair[1], reverse=True)

    welded = len(indexed) <= 1
    return [
        Part(
            id=f"{id_prefix}_{seq:03d}",
            connected_component_ids=[orig_idx],
            face_count=face_count,
            is_uncertain=welded,
        )
        for seq, (orig_idx, face_count) in enumerate(indexed)
    ]


def _split_mesh(mesh: trimesh.Trimesh | trimesh.Scene) -> list[Any]:
    """Return the connected-component sub-meshes of ``mesh`` (duck-typed).

    Avoids importing trimesh at runtime: the caller already holds a trimesh
    object, so we detect a Scene (``geometry`` but no ``split``) and otherwise
    require a mesh exposing ``split`` and ``faces``. The object is handled as
    ``Any`` because trimesh's own annotations collapse meshes to a loose
    ``Geometry`` base type.
    """
    obj: Any = mesh
    if hasattr(obj, "geometry") and not hasattr(obj, "split"):
        # Scene -> single concatenated mesh before connected-component analysis.
        # to_geometry() is the current API; dump(concatenate=True) is the
        # pre-deprecation fallback for older trimesh 4.x.
        obj = obj.to_geometry() if hasattr(obj, "to_geometry") else obj.dump(concatenate=True)
    if not (hasattr(obj, "split") and hasattr(obj, "faces")):
        raise TypeError(f"expected a trimesh Trimesh or Scene, got {type(mesh).__name__}")
    return list(obj.split(only_watertight=False))
