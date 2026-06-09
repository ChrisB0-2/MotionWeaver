"""Axis utilities and kinematic-graph planner.

Pivot inference itself is covered by ``test_pivots.py`` (trimesh-gated); this
file keeps the dependency-free pieces: axis helpers and the planner.
"""

from __future__ import annotations

from typing import Any

import pytest

from mw_core import MotionSpec, normalize_spec
from mw_core.geometry.axes import cardinal_to_vector
from mw_core.rig.planner import plan


def test_cardinal_axis_conversion() -> None:
    assert cardinal_to_vector("Z") == (0.0, 0.0, 1.0)
    assert cardinal_to_vector("-Y") == (0.0, -1.0, 0.0)
    with pytest.raises(ValueError):
        cardinal_to_vector("Q")


def test_planner_builds_tree_with_expected_roots(antenna_spec_dict: dict[str, Any]) -> None:
    spec = normalize_spec(MotionSpec.model_validate(antenna_spec_dict))
    graph = plan(spec)
    root_ids = {root.part_id for root in graph.roots}
    # base and dish_yoke are never a child_part in the example, so both are roots.
    assert root_ids == {"base", "dish_yoke"}
    assert len(graph.iter_nodes()) == len(spec.parts)
