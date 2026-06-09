"""Operators: import mesh, build preview rig, bake & export.

Each operator delegates real work to the dedicated helper modules so the
operator bodies stay thin.
"""

from __future__ import annotations

import bpy  # type: ignore[import-not-found]


class MW_OT_import_mesh(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "motionweaver.import_mesh"
    bl_label = "Import Mesh"
    bl_description = "Import the source mesh and extract candidate parts"

    def execute(self, context: object) -> set[str]:  # noqa: ARG002
        from mw_blender.addon import import_mesh

        import_mesh.run(context)  # TODO
        self.report({"INFO"}, "MotionWeaver: import_mesh not implemented yet")
        return {"CANCELLED"}


class MW_OT_build_rig(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "motionweaver.build_rig"
    bl_label = "Build Preview Rig"
    bl_description = "Compile the motion_spec into a deterministic Blender preview rig"

    def execute(self, context: object) -> set[str]:  # noqa: ARG002
        from mw_blender.addon import build_rig

        build_rig.run(context)  # TODO
        self.report({"INFO"}, "MotionWeaver: build_rig not implemented yet")
        return {"CANCELLED"}


class MW_OT_bake_export(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "motionweaver.bake_export"
    bl_label = "Bake & Export"
    bl_description = "Bake clips to TRS tracks and export GLB + sidecar manifest"

    def execute(self, context: object) -> set[str]:  # noqa: ARG002
        from mw_blender.addon import bake_export

        bake_export.run(context)  # TODO
        self.report({"INFO"}, "MotionWeaver: bake_export not implemented yet")
        return {"CANCELLED"}


_CLASSES = (MW_OT_import_mesh, MW_OT_build_rig, MW_OT_bake_export)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
