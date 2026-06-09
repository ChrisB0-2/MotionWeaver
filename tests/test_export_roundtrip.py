"""Sidecar manifest round-trip and axis normalization."""

from __future__ import annotations

import math
from typing import Any

import pytest
from mw_core import MotionSpec, normalize_spec
from mw_core.exporters.manifest_export import build_manifest, spec_from_manifest
from mw_core.motion_spec.normalization import normalize_axis


def test_manifest_roundtrip_preserves_spec(antenna_spec_dict: dict[str, Any]) -> None:
    spec = MotionSpec.model_validate(antenna_spec_dict)
    manifest = build_manifest(spec)
    assert manifest["kind"] == "motionweaver.manifest"
    recovered = spec_from_manifest(manifest)
    assert recovered == spec


def test_spec_from_manifest_rejects_foreign_payload() -> None:
    with pytest.raises(ValueError):
        spec_from_manifest({"kind": "something.else", "motion_spec": {}})


def test_normalize_makes_axes_unit_length(antenna_spec_dict: dict[str, Any]) -> None:
    raw = MotionSpec.model_validate(antenna_spec_dict)
    raw.joints[0].axis = [0.0, 0.0, 5.0]
    spec = normalize_spec(raw)
    norm = math.sqrt(sum(c * c for c in spec.joints[0].axis))
    assert math.isclose(norm, 1.0, rel_tol=1e-9)


def test_normalize_axis_rejects_zero_vector() -> None:
    with pytest.raises(ValueError):
        normalize_axis([0.0, 0.0, 0.0])
