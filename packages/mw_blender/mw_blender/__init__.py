"""MotionWeaver Blender add-on entry point.

Registers operators, panels, and properties. Heavy parsing/analysis is delegated
to a sidecar service / ``mw_core``; this add-on is the UX layer only.
"""

from __future__ import annotations

bl_info = {
    "name": "MotionWeaver",
    "author": "MotionWeaver contributors",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > MotionWeaver",
    "description": "AI-assisted motion compiler for rigid mechanical assets",
    "category": "Rigging",
}

# Import submodules lazily inside register() so the file can be inspected without
# bpy present (e.g. by linters running outside Blender).


def register() -> None:
    from mw_blender.addon import operators, panels, properties

    properties.register()
    operators.register()
    panels.register()


def unregister() -> None:
    from mw_blender.addon import operators, panels, properties

    panels.unregister()
    operators.unregister()
    properties.unregister()
