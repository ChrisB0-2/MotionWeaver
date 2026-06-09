"""Shared test fixtures, spec builders, and path helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mw_core import MotionSpec, validate_spec

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
SCHEMA_PATH = REPO_ROOT / "schemas" / "motion_spec.schema.json"

Keyframes = list[tuple[float, float] | tuple[float, float, str]]


def make_spec(
    *,
    joint_type: str = "hinge",
    axis: list[float] | None = None,
    pivot: list[float] | None = None,
    pivot_space: str = "world",
    control_property: str = "angle_deg",
    keyframes: Keyframes | None = None,
    duration_s: float | None = 1.0,
    controls: list[dict[str, Any]] | None = None,
    channels: list[dict[str, Any]] | None = None,
    up_axis: str = "Z",
    unit_scale_meters: float = 1.0,
) -> MotionSpec:
    """Build a minimal validated two-part spec: base --j1--> arm, control c1, clip clip1."""
    if keyframes is None:
        keyframes = [(0.0, 0.0), (1.0, 90.0)]
    keyframe_dicts = [
        {"t": kf[0], "value": kf[1], "interp": kf[2] if len(kf) == 3 else "linear"}
        for kf in keyframes
    ]
    if controls is None:
        controls = [
            {"id": "c1", "label": "Control 1", "joint_id": "j1", "property": control_property}
        ]
    if channels is None:
        channels = [{"control_id": "c1", "keyframes": keyframe_dicts}]
    payload = {
        "schema_version": "0.1.0",
        "asset_id": "baker_test",
        "coordinate_system": {
            "up_axis": up_axis,
            "forward_axis": "Y",
            "unit_scale_meters": unit_scale_meters,
        },
        "parts": [
            {"id": "base", "name": "Base", "selector": {"object_names": ["Base"]}},
            {"id": "arm", "name": "Arm", "selector": {"object_names": ["Arm"]}},
        ],
        "joints": [
            {
                "id": "j1",
                "type": joint_type,
                "parent_part": "base",
                "child_part": "arm",
                "pivot": {"space": pivot_space, "position": pivot or [0.0, 0.0, 0.0]},
                "axis": axis or [0.0, 0.0, 1.0],
            }
        ],
        "controls": controls,
        "clips": [
            {"id": "clip1", "name": "Clip 1", "duration_s": duration_s, "channels": channels}
        ],
    }
    return validate_spec(MotionSpec.model_validate(payload))


@pytest.fixture
def antenna_spec_dict() -> dict[str, Any]:
    return json.loads((EXAMPLES_DIR / "antenna_motion_spec.json").read_text(encoding="utf-8"))


@pytest.fixture
def motion_spec_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
