"""The example spec must satisfy both the JSON Schema and the Pydantic model,
and round-trip losslessly through the model."""

from __future__ import annotations

from typing import Any

import jsonschema

from mw_core import MotionSpec


def test_antenna_example_matches_json_schema(
    antenna_spec_dict: dict[str, Any], motion_spec_schema: dict[str, Any]
) -> None:
    jsonschema.validate(instance=antenna_spec_dict, schema=motion_spec_schema)


def test_antenna_example_parses_into_model(antenna_spec_dict: dict[str, Any]) -> None:
    spec = MotionSpec.model_validate(antenna_spec_dict)
    assert spec.asset_id == "antenna_demo_a01"
    assert len(spec.parts) == 5
    assert len(spec.joints) == 3
    assert {c.id for c in spec.controls} == {"ctrl_yaw", "ctrl_pitch", "ctrl_hatch"}


def test_model_roundtrip_is_stable(antenna_spec_dict: dict[str, Any]) -> None:
    spec = MotionSpec.model_validate(antenna_spec_dict)
    reparsed = MotionSpec.model_validate(spec.model_dump(mode="json", exclude_none=True))
    assert reparsed == spec


def test_unknown_field_is_rejected(antenna_spec_dict: dict[str, Any]) -> None:
    import pydantic
    import pytest

    bad = dict(antenna_spec_dict)
    bad["unexpected_field"] = True
    with pytest.raises(pydantic.ValidationError):
        MotionSpec.model_validate(bad)
