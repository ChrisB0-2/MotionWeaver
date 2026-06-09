"""Pivot/axis candidate inference from part contact regions.

Skipped entirely when trimesh (the optional "geometry" extra) is not installed.
"""

from __future__ import annotations

import math

import pytest

from mw_core.geometry.pivots import pivot_candidates_from_contact

trimesh = pytest.importorskip("trimesh")


def _stacked_boxes() -> tuple[trimesh.Trimesh, trimesh.Trimesh]:
    """A 1x1 turret centered on a 2x2 base: planar square contact at z=0.5."""
    base = trimesh.creation.box(extents=(2.0, 2.0, 1.0))
    turret = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    turret.apply_translation([0.0, 0.0, 1.0])
    return base, turret


def _edge_touching_boxes() -> tuple[trimesh.Trimesh, trimesh.Trimesh]:
    """Two unit boxes sharing exactly one edge along X at (y, z) = (0.5, 0.5)."""
    a = trimesh.creation.box()
    b = trimesh.creation.box()
    b.apply_translation([0.0, 1.0, 1.0])
    return a, b


def test_planar_contact_proposes_spin_about_plane_normal() -> None:
    base, turret = _stacked_boxes()
    candidates = pivot_candidates_from_contact(base, turret)
    # Both interpretations are offered (plane-normal spin + weak in-plane
    # hinge), ranked so the better-supported one comes first.
    assert len(candidates) == 2
    top = candidates[0]
    assert top.axis == pytest.approx((0.0, 0.0, 1.0), abs=1e-6)
    assert top.position == pytest.approx((0.0, 0.0, 0.5), abs=1e-6)
    assert top.confidence > candidates[1].confidence


def test_edge_contact_proposes_hinge_along_edge() -> None:
    a, b = _edge_touching_boxes()
    candidates = pivot_candidates_from_contact(a, b)
    # Collinear contact has no usable contact-plane normal: one candidate only.
    assert len(candidates) == 1
    hinge = candidates[0]
    assert hinge.axis == pytest.approx((1.0, 0.0, 0.0), abs=1e-6)
    assert hinge.position == pytest.approx((0.0, 0.5, 0.5), abs=1e-6)
    assert hinge.confidence >= 0.8


def test_cylinder_on_plate_proposes_spin_about_cylinder_axis() -> None:
    plate = trimesh.creation.box(extents=(4.0, 4.0, 0.2))  # top face at z=0.1
    wheel = trimesh.creation.cylinder(radius=0.5, height=1.0)
    wheel.apply_translation([0.0, 0.0, 0.6])  # base rim rests on the plate top
    candidates = pivot_candidates_from_contact(plate, wheel)
    top = candidates[0]
    assert top.axis == pytest.approx((0.0, 0.0, 1.0), abs=1e-6)
    assert top.position == pytest.approx((0.0, 0.0, 0.1), abs=1e-6)


def test_separated_parts_yield_no_candidates() -> None:
    a = trimesh.creation.box()
    b = trimesh.creation.box()
    b.apply_translation([5.0, 0.0, 0.0])
    assert pivot_candidates_from_contact(a, b) == []


def test_explicit_tolerance_bridges_modeled_clearance() -> None:
    a = trimesh.creation.box()
    b = trimesh.creation.box()
    b.apply_translation([1.05, 0.0, 0.0])  # 0.05 gap between the facing sides
    # The default tolerance (~0.5% of the combined bbox diagonal) must not
    # silently bridge a real modeled gap...
    assert pivot_candidates_from_contact(a, b) == []
    # ...but an explicit tolerance treats it as clearance: the two near faces
    # form a planar region whose normal is the X axis, centered in the gap.
    candidates = pivot_candidates_from_contact(a, b, tolerance=0.1)
    assert candidates
    top = candidates[0]
    assert top.axis == pytest.approx((1.0, 0.0, 0.0), abs=1e-6)
    assert top.position[0] == pytest.approx(0.525, abs=1e-6)
    with pytest.raises(ValueError):
        pivot_candidates_from_contact(a, b, tolerance=-1.0)


def test_point_contact_yields_single_low_confidence_candidate() -> None:
    a = trimesh.creation.box()
    b = trimesh.creation.box()
    b.apply_translation([1.0, 1.0, 1.0])  # touches only at corner (.5, .5, .5)
    candidates = pivot_candidates_from_contact(a, b)
    assert len(candidates) == 1
    only = candidates[0]
    assert only.position == pytest.approx((0.5, 0.5, 0.5), abs=1e-6)
    # Axis is an explicit guess (parent->child direction), flagged as such.
    unit = 1.0 / math.sqrt(3.0)
    assert only.axis == pytest.approx((unit, unit, unit), abs=1e-6)
    assert only.confidence <= 0.25
    assert "point" in only.rationale.lower()


def test_candidate_invariants_hold_across_scenarios() -> None:
    scenarios = [_stacked_boxes(), _edge_touching_boxes()]
    for parent, child in scenarios:
        for cand in pivot_candidates_from_contact(parent, child):
            assert math.isclose(math.hypot(*cand.axis), 1.0, abs_tol=1e-9)
            assert 0.0 < cand.confidence <= 0.9
            assert cand.rationale.strip()


def test_non_mesh_inputs_raise_type_error() -> None:
    box = trimesh.creation.box()
    with pytest.raises(TypeError):
        pivot_candidates_from_contact(object(), box)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        pivot_candidates_from_contact(box, object())  # type: ignore[arg-type]
    # Scenes must be split into parts first; pivots work on single meshes.
    with pytest.raises(TypeError):
        pivot_candidates_from_contact(trimesh.Scene(), box)  # type: ignore[arg-type]
