"""Mesh importers.

Deterministic-first: prefer Blender's own importers when running inside the
add-on, and ``trimesh`` for the headless core. Returns a normalized in-memory
representation that downstream analysis consumes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ImportedMesh:
    """A normalized, backend-agnostic view of imported geometry."""

    source_path: Path
    # Object/sub-mesh names as found in the source file, used by Part selectors.
    object_names: list[str] = field(default_factory=list)
    material_names: list[str] = field(default_factory=list)
    # Populated by part_graph.split_connected_components.
    connected_component_count: int = 0


def import_mesh(path: str | Path) -> ImportedMesh:
    """Import a mesh file (``.glb``/``.gltf``/``.obj``/...) into an ImportedMesh.

    TODO: implement with ``trimesh.load`` (headless) and a Blender-native path in
    ``mw_blender``. Must preserve object and material names so Part selectors can
    resolve against them.
    """
    raise NotImplementedError("mesh import not implemented yet")
