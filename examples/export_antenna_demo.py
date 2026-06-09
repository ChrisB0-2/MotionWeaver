"""Export the antenna example with placeholder geometry to a playable GLB.

Usage::

    uv run python examples/export_antenna_demo.py [out_dir]

The repo does not ship the real antenna source mesh, so this builds simple
placeholder parts sized and placed to match the spec's pivots, then runs the
deterministic pipeline end to end: validate -> normalize -> plan -> bake ->
export GLB + sidecar manifest. Drop the GLB into any glTF viewer (for example
gltf-viewer.donmccurdy.com) and play "scan_loop" or "maintenance_open".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import trimesh

from mw_core import MotionSpec, normalize_spec, validate_spec
from mw_core.exporters.gltf_export import export_glb
from mw_core.exporters.manifest_export import build_manifest
from mw_core.rig.baker import bake
from mw_core.rig.planner import plan

EXAMPLES_DIR = Path(__file__).resolve().parent
SPEC_PATH = EXAMPLES_DIR / "antenna_motion_spec.json"


def build_demo_meshes() -> dict[str, Any]:
    """Placeholder rigid parts matching the spec's pivots (Z-up world, meters)."""
    base = trimesh.creation.cylinder(radius=0.3, height=0.5)
    base.apply_translation((0.0, 0.0, 0.25))
    # Mast sits on the base; its yaw pivot is at z=0.25.
    mast = trimesh.creation.cylinder(radius=0.05, height=1.0)
    mast.apply_translation((0.0, 0.0, 0.75))
    yoke = trimesh.creation.box(extents=(0.2, 0.1, 0.2))
    yoke.apply_translation((0.0, 0.1, 1.3))
    # Dish hangs off the yoke; its pitch pivot is at (0, 0.15, 1.35).
    dish = trimesh.creation.cylinder(radius=0.45, height=0.05)
    dish.apply_translation((0.0, 0.15, 1.35))
    # Hatch plate swings about a Y-axis hinge at (-0.22, -0.18, 0.32).
    hatch = trimesh.creation.box(extents=(0.04, 0.16, 0.2))
    hatch.apply_translation((-0.22, -0.18, 0.42))
    return {"base": base, "mast": mast, "dish_yoke": yoke, "dish": dish, "service_hatch": hatch}


def export_demo(out_dir: str | Path) -> tuple[Path, Path]:
    """Run the full pipeline; return (glb_path, manifest_path)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    spec = validate_spec(normalize_spec(MotionSpec.model_validate(raw)))
    graph = plan(spec)
    baked = bake(spec, graph)
    glb_path = export_glb(out / "antenna_demo.glb", spec, graph, baked, meshes=build_demo_meshes())
    manifest_path = out / "antenna_demo.manifest.json"
    manifest_path.write_text(json.dumps(build_manifest(spec), indent=2), encoding="utf-8")
    return glb_path, manifest_path


def main(argv: list[str]) -> int:
    out_dir = Path(argv[1]) if len(argv) > 1 else EXAMPLES_DIR / "out"
    glb_path, manifest_path = export_demo(out_dir)
    print(f"wrote {glb_path}")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
