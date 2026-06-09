"""The MotionWeaver sidebar panel in the 3D viewport."""

from __future__ import annotations

import bpy  # type: ignore[import-not-found]


class MW_PT_main(bpy.types.Panel):  # type: ignore[misc]
    bl_label = "MotionWeaver"
    bl_idname = "MW_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MotionWeaver"

    def draw(self, context: object) -> None:
        layout = self.layout  # type: ignore[attr-defined]
        props = context.scene.motionweaver
        layout.prop(props, "source_mesh_path")
        layout.prop(props, "spec_path")
        layout.separator()
        layout.operator("motionweaver.import_mesh")
        layout.operator("motionweaver.build_rig")
        layout.operator("motionweaver.bake_export")


_CLASSES = (MW_PT_main,)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
