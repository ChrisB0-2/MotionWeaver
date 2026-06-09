"""Semantic validation: the valid example passes; deliberately broken specs fail
with the expected issue."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from mw_core import MotionSpec, SemanticError, normalize_spec, validate_spec
from mw_core.motion_spec import semantic_issues


def test_valid_example_passes(antenna_spec_dict: dict[str, Any]) -> None:
    spec = normalize_spec(MotionSpec.model_validate(antenna_spec_dict))
    assert semantic_issues(spec) == []
    assert validate_spec(spec) is spec


def test_unknown_joint_part_reference_fails(antenna_spec_dict: dict[str, Any]) -> None:
    bad = copy.deepcopy(antenna_spec_dict)
    bad["joints"][0]["child_part"] = "ghost_part"
    spec = MotionSpec.model_validate(bad)
    issues = semantic_issues(spec)
    assert any("unknown child_part" in i for i in issues)


def test_kinematic_cycle_is_detected(antenna_spec_dict: dict[str, Any]) -> None:
    bad = copy.deepcopy(antenna_spec_dict)
    # base -> mast already exists; add mast -> base to form a cycle.
    bad["joints"].append(
        {
            "id": "cycle_joint",
            "type": "hinge",
            "parent_part": "mast",
            "child_part": "base",
            "pivot": {"space": "world", "position": [0.0, 0.0, 0.0]},
            "axis": [0.0, 0.0, 1.0],
        }
    )
    spec = MotionSpec.model_validate(bad)
    issues = semantic_issues(spec)
    assert any("cycle" in i for i in issues)


def test_degenerate_axis_fails(antenna_spec_dict: dict[str, Any]) -> None:
    bad = copy.deepcopy(antenna_spec_dict)
    bad["joints"][0]["axis"] = [0.0, 0.0, 0.0]
    spec = MotionSpec.model_validate(bad)
    issues = semantic_issues(spec)
    assert any("degenerate" in i for i in issues)


def test_hinge_with_linear_limits_fails(antenna_spec_dict: dict[str, Any]) -> None:
    bad = copy.deepcopy(antenna_spec_dict)
    bad["joints"][0]["limits"] = {"min_m": 0.0, "max_m": 1.0}
    spec = MotionSpec.model_validate(bad)
    issues = semantic_issues(spec)
    assert any("linear limits" in i for i in issues)


def test_inverted_hinge_limits_fail(antenna_spec_dict: dict[str, Any]) -> None:
    bad = copy.deepcopy(antenna_spec_dict)
    bad["joints"][0]["limits"] = {"min_deg": 90.0, "max_deg": -90.0}
    spec = MotionSpec.model_validate(bad)
    assert any("min_deg > max_deg" in i for i in semantic_issues(spec))


def test_control_referencing_missing_joint_fails(antenna_spec_dict: dict[str, Any]) -> None:
    bad = copy.deepcopy(antenna_spec_dict)
    bad["controls"][0]["joint_id"] = "no_such_joint"
    spec = MotionSpec.model_validate(bad)
    assert any("unknown joint" in i for i in semantic_issues(spec))


def test_clip_referencing_missing_control_fails(antenna_spec_dict: dict[str, Any]) -> None:
    bad = copy.deepcopy(antenna_spec_dict)
    bad["clips"][0]["channels"][0]["control_id"] = "no_such_control"
    spec = MotionSpec.model_validate(bad)
    assert any("unknown control" in i for i in semantic_issues(spec))


def test_validate_spec_raises_semantic_error(antenna_spec_dict: dict[str, Any]) -> None:
    bad = copy.deepcopy(antenna_spec_dict)
    bad["controls"][0]["joint_id"] = "no_such_joint"
    spec = MotionSpec.model_validate(bad)
    with pytest.raises(SemanticError):
        validate_spec(spec)
