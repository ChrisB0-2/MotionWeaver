"""Pivot solver and axis utilities.

The pivot solver itself is a TODO-backed stub; this test pins its contract
(raises until implemented) and exercises the implemented axis helpers and the
kinematic-graph planner.
"""

from __future__ import annotations

from typing import Any

import pytest

from mw_core import MotionSpec, normalize_spec
from mw_core.geometry.axes import cardinal_to_vector
from mw_core.geometry.pivots import pivot_candidates_from_contact
from mw_core.rig.planner import plan


def test_cardinal_axis_conversion() -> None:
    assert cardinal_to_vector("Z") == (0.0, 0.0, 1.0)
    assert cardinal_to_vector("-Y") == (0.0, -1.0, 0.0)
    with pytest.raises(ValueError):
        cardinal_to_vector("Q")


def test_pivot_solver_contract_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError):
        pivot_candidates_from_contact(object(), object())


def test_planner_builds_tree_with_expected_roots(antenna_spec_dict: dict[str, Any]) -> None:
    spec = normalize_spec(MotionSpec.model_validate(antenna_spec_dict))
    graph = plan(spec)
    root_ids = {root.part_id for root in graph.roots}
    # base and dish_yoke are never a child_part in the example, so both are roots.
    assert root_ids == {"base", "dish_yoke"}
    assert len(graph.iter_nodes()) == len(spec.parts)
