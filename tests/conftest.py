"""Shared test fixtures and path helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
SCHEMA_PATH = REPO_ROOT / "schemas" / "motion_spec.schema.json"


@pytest.fixture
def antenna_spec_dict() -> dict[str, Any]:
    return json.loads((EXAMPLES_DIR / "antenna_motion_spec.json").read_text(encoding="utf-8"))


@pytest.fixture
def motion_spec_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
