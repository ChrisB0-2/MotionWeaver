"""Connected-component splitting via trimesh.

Skipped entirely when trimesh (the optional "geometry" extra) is not installed.
"""

from __future__ import annotations

import pytest

from mw_core.geometry.part_graph import split_connected_components

trimesh = pytest.importorskip("trimesh")


def _two_disconnected_boxes() -> trimesh.Trimesh:
    a = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    b = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    b.apply_translation([5.0, 0.0, 0.0])
    return trimesh.util.concatenate([a, b])


def test_two_disconnected_parts_are_split() -> None:
    parts = split_connected_components(_two_disconnected_boxes())
    assert len(parts) == 2
    assert all(not p.is_uncertain for p in parts)
    assert all(p.face_count > 0 for p in parts)
    # ids are sequential; each maps back to a distinct source component.
    assert [p.id for p in parts] == ["part_000", "part_001"]
    assert {ci for p in parts for ci in p.connected_component_ids} == {0, 1}


def test_welded_single_mesh_is_flagged_uncertain() -> None:
    parts = split_connected_components(trimesh.creation.box())
    assert len(parts) == 1
    assert parts[0].is_uncertain is True


def test_min_faces_filters_small_components() -> None:
    # A high threshold discards both boxes (12 triangles each).
    assert split_connected_components(_two_disconnected_boxes(), min_faces=10_000) == []
    # min_faces=0 keeps everything.
    assert len(split_connected_components(_two_disconnected_boxes(), min_faces=0)) == 2


def test_scene_input_is_concatenated_then_split() -> None:
    scene = trimesh.Scene()
    a = trimesh.creation.box()
    b = trimesh.creation.box()
    b.apply_translation([5.0, 0.0, 0.0])
    scene.add_geometry(a, geom_name="a")
    scene.add_geometry(b, geom_name="b")
    parts = split_connected_components(scene)
    assert len(parts) == 2


def test_parts_sorted_largest_first() -> None:
    big = trimesh.creation.icosphere(subdivisions=3)  # many faces
    small = trimesh.creation.box()  # 12 faces
    small.apply_translation([10.0, 0.0, 0.0])
    parts = split_connected_components(trimesh.util.concatenate([small, big]))
    assert len(parts) == 2
    assert parts[0].face_count >= parts[1].face_count


def test_min_faces_reducing_to_one_part_is_flagged_uncertain() -> None:
    """A mesh filtered down to one surviving component is flagged uncertain.

    is_uncertain means "connected-component analysis could not confirm rigid
    boundaries" — a single survivor after min_faces filtering is structurally
    indistinguishable from a welded mesh as far as the planner is concerned.
    """
    big = trimesh.creation.icosphere(subdivisions=3)
    small = trimesh.creation.box()  # 12 faces, below the threshold
    small.apply_translation([10.0, 0.0, 0.0])
    parts = split_connected_components(trimesh.util.concatenate([small, big]), min_faces=1000)
    assert len(parts) == 1
    assert parts[0].is_uncertain is True


def test_non_mesh_input_raises_type_error() -> None:
    with pytest.raises(TypeError):
        split_connected_components(object())  # type: ignore[arg-type]
