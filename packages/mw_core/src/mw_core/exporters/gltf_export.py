"""GLB/glTF export of baked clips.

Writes node TRS animation tracks and mirrors only stable ids into glTF
``extras``. Blender-specific rig semantics are excluded; they live in the
sidecar manifest.
"""

from __future__ import annotations

from pathlib import Path

from mw_core.rig.baker import BakedClip


def export_glb(
    out_path: str | Path,
    baked_clips: list[BakedClip],
    *,
    embed_stable_ids: bool = True,
) -> Path:
    """Write a ``.glb`` with baked TRS animation tracks.

    TODO: implement using ``glTF Transform`` (preferred) or pygltflib. Each
    BakedClip becomes a glTF animation; each BakedTrack maps to TRS channels on
    the corresponding node. When ``embed_stable_ids`` is set, mirror part/control
    ids into node ``extras`` (stable ids only, never the canonical semantics).
    """
    raise NotImplementedError("glTF export not implemented yet")
