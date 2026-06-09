"""Mesh import via trimesh.load.

Skipped entirely when trimesh (the optional "geometry" extra) is not installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mw_core.geometry.importers import ImportedMesh, import_mesh
from mw_core.geometry.part_graph import split_connected_components

trimesh = pytest.importorskip("trimesh")


def test_import_glb_returns_imported_mesh(tmp_path: Path) -> None:
    path = tmp_path / "box.glb"
    trimesh.creation.box().export(path)
    imported = import_mesh(path)
    assert isinstance(imported, ImportedMesh)
    assert imported.source_path == path
    assert imported.connected_component_count == 1
    assert imported.geometry is not None


def test_import_obj_uses_file_stem_as_object_name(tmp_path: Path) -> None:
    # OBJ loads as a bare Trimesh (no scene graph), so the file stem is the
    # only object name available.
    path = tmp_path / "antenna.obj"
    trimesh.creation.box().export(path)
    imported = import_mesh(path)
    assert imported.object_names == ["antenna"]


def test_import_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        import_mesh(tmp_path / "does_not_exist.glb")


def test_import_scene_glb_preserves_object_names(tmp_path: Path) -> None:
    scene = trimesh.Scene()
    a = trimesh.creation.box()
    b = trimesh.creation.box()
    b.apply_translation([5.0, 0.0, 0.0])
    scene.add_geometry(a, geom_name="body")
    scene.add_geometry(b, geom_name="lid")
    path = tmp_path / "two.glb"
    scene.export(path)

    imported = import_mesh(path)
    assert sorted(imported.object_names) == ["body", "lid"]
    assert imported.connected_component_count == 2


def test_import_glb_with_named_material_extracts_material_name(tmp_path: Path) -> None:
    # A PBR material name survives the GLB round-trip and lands in
    # material_names (the true-positive path of _material_names; plain
    # ColorVisuals files are covered by the tests above yielding []).
    mesh = trimesh.creation.box()
    mesh.visual = trimesh.visual.TextureVisuals(
        material=trimesh.visual.material.PBRMaterial(name="HullPaint")
    )
    path = tmp_path / "painted.glb"
    trimesh.Scene({"Hull": mesh}).export(path)

    imported = import_mesh(path)
    assert imported.material_names == ["HullPaint"]


def test_imported_geometry_feeds_split_connected_components(tmp_path: Path) -> None:
    # End-to-end: file -> ImportedMesh -> split_connected_components -> [Part].
    scene = trimesh.Scene()
    a = trimesh.creation.box()
    b = trimesh.creation.box()
    b.apply_translation([5.0, 0.0, 0.0])
    scene.add_geometry(a, geom_name="body")
    scene.add_geometry(b, geom_name="lid")
    path = tmp_path / "two.glb"
    scene.export(path)

    imported = import_mesh(path)
    parts = split_connected_components(imported.geometry)
    assert len(parts) == imported.connected_component_count == 2
    assert all(not p.is_uncertain for p in parts)
