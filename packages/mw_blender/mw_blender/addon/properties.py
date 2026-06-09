"""Scene-level properties for the MotionWeaver add-on.

TODO: store the current motion_spec path, sidecar service URL, source mesh path,
and per-joint preview control values as Blender custom properties.
"""

from __future__ import annotations

import bpy  # type: ignore[import-not-found]


class MotionWeaverSceneProps(bpy.types.PropertyGroup):  # type: ignore[misc]
    spec_path: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="motion_spec",
        subtype="FILE_PATH",
        description="Path to the canonical motion_spec JSON",
    )
    source_mesh_path: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Source Mesh",
        subtype="FILE_PATH",
    )


_CLASSES = (MotionWeaverSceneProps,)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.motionweaver = bpy.props.PointerProperty(type=MotionWeaverSceneProps)


def unregister() -> None:
    del bpy.types.Scene.motionweaver
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
