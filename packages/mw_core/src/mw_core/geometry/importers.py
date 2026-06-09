"""Mesh importers.

Deterministic-first: prefer Blender's own importers when running inside the
add-on, and ``trimesh`` for the headless core. Returns a normalized in-memory
representation that downstream analysis consumes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mw_core.geometry.part_graph import _split_mesh


@dataclass
class ImportedMesh:
    """A normalized, backend-agnostic view of imported geometry."""

    source_path: Path
    # Object/sub-mesh names as found in the source file, used by Part selectors.
    object_names: list[str] = field(default_factory=list)
    material_names: list[str] = field(default_factory=list)
    # Number of connected components (same splitting as
    # part_graph.split_connected_components).
    connected_component_count: int = 0
    # The loaded trimesh object (Trimesh or Scene), kept so downstream analysis
    # (split_connected_components, pivot inference) does not need to reload the
    # file. Typed Any because trimesh is an optional "geometry" extra.
    geometry: Any = None


def import_mesh(path: str | Path) -> ImportedMesh:
    """Import a mesh file (``.glb``/``.gltf``/``.obj``/...) into an ImportedMesh.

    Loads via ``trimesh.load`` without forcing concatenation, so multi-object
    files (e.g. GLB with named nodes) come back as a Scene and their object and
    material names are preserved for Part selectors to resolve against.

    Args:
        path: path to a mesh file in any format trimesh can read.

    Raises:
        ImportError: if trimesh (the optional ``geometry`` extra) is missing.
        FileNotFoundError: if ``path`` does not exist.
        TypeError: if the file loads as something other than a mesh or scene
            (e.g. a path/point-cloud format).
    """
    try:
        import trimesh
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            "import_mesh requires the optional 'geometry' extra (pip install mw-core[geometry])"
        ) from exc

    resolved = Path(path)
    if not resolved.is_file():
        raise FileNotFoundError(f"mesh file not found: {resolved}")

    loaded: Any = trimesh.load(str(resolved))

    if hasattr(loaded, "geometry") and not hasattr(loaded, "split"):
        # Scene: object names are the scene's geometry keys.
        object_names = [str(name) for name in loaded.geometry]
        sub_meshes = list(loaded.geometry.values())
    else:
        # Single mesh: the file stem is the only name we have.
        object_names = [resolved.stem]
        sub_meshes = [loaded]

    material_names = sorted({name for sub in sub_meshes for name in _material_names(sub)})
    # _split_mesh validates the loaded type (raises TypeError otherwise) and
    # applies the same Scene-concatenation + split as split_connected_components.
    component_count = len(_split_mesh(loaded))

    return ImportedMesh(
        source_path=resolved,
        object_names=object_names,
        material_names=material_names,
        connected_component_count=component_count,
        geometry=loaded,
    )


def _material_names(geom: Any) -> list[str]:
    """Best-effort material name extraction from one trimesh geometry.

    trimesh visuals vary (``TextureVisuals`` carry a material, plain
    ``ColorVisuals`` do not), so walk the attribute chain defensively and
    return [] rather than raising.
    """
    visual = getattr(geom, "visual", None)
    material = getattr(visual, "material", None)
    name = getattr(material, "name", None)
    return [name] if isinstance(name, str) and name else []
