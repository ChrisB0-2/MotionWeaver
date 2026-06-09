# mw_blender

The MotionWeaver Blender add-on. Provides the in-Blender UX: import mesh,
inspect/confirm parts and pivots, build a deterministic preview rig, and
bake/export to GLB + sidecar manifest.

This package is **not** part of the uv workspace: it imports `bpy`, which only
exists inside Blender. Install it by zipping the `mw_blender/` folder and
enabling it via *Edit > Preferences > Add-ons*, or symlink it into Blender's
`scripts/addons` directory. Baseline target: **Blender 4.5 LTS**.

The add-on consumes the canonical kinematic graph produced by `mw_core`; it does
not own the spec, and it never executes model-generated Python.
