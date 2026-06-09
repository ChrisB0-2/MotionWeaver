"""Preview-rig control helpers (drivers, custom properties, limit clamping).

These are Blender-only conveniences. Anything defined here must be reproducible
as baked TRS tracks at export time, or it is preview-only and excluded from GLB.
"""

from __future__ import annotations


def add_hinge_control(empty: object, joint: object) -> None:
    """Add a custom-property angle control + driver to a hinge pivot empty.

    TODO: implement with bpy custom properties and a rotation driver respecting
    joint limits.
    """
    raise NotImplementedError("preview hinge control not implemented yet")
