"""Save the authored Blender scene as a ``.blend`` file.

This is the editable DCC artifact (with preview-only drivers/controls intact),
distinct from the baked, portable GLB. Only meaningful inside Blender, so it is
invoked from ``mw_blender``.
"""

from __future__ import annotations

from pathlib import Path


def export_blend(out_path: str | Path) -> Path:
    """Save the current Blender scene to ``out_path``.

    TODO: implement in the Blender add-on context via
    ``bpy.ops.wm.save_as_mainfile``. Must not be called from the headless core.
    """
    raise NotImplementedError("blend export must run inside Blender (mw_blender)")
