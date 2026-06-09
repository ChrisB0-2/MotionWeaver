"""The antenna demo example exports a playable GLB + manifest end to end."""

from __future__ import annotations

import importlib.util
import json
import struct
from pathlib import Path
from types import ModuleType

import pytest

from conftest import REPO_ROOT
from mw_core.exporters.manifest_export import spec_from_manifest


def _load_example_module() -> ModuleType:
    path = REPO_ROOT / "examples" / "export_antenna_demo.py"
    module_spec = importlib.util.spec_from_file_location("export_antenna_demo", path)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_antenna_demo_exports_playable_glb_and_manifest(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    demo = _load_example_module()
    glb_path, manifest_path = demo.export_demo(tmp_path)
    assert glb_path.exists()
    assert manifest_path.exists()

    # The GLB loads as a 5-part scene.
    scene = trimesh.load(glb_path)
    assert len(scene.geometry) == 5

    # Both clips are present as animations (trimesh ignores them, so parse the JSON chunk).
    data = glb_path.read_bytes()
    json_length = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20 : 20 + json_length].decode("utf-8"))
    assert [a["name"] for a in doc["animations"]] == ["scan_loop", "maintenance_open"]

    # The sidecar manifest round-trips back to the validated spec.
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    spec = spec_from_manifest(manifest)
    assert spec.asset_id == "antenna_demo_a01"
    assert [c.id for c in spec.clips] == ["scan_loop", "maintenance_open"]
