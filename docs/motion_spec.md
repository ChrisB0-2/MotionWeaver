# motion_spec

The `motion_spec` is MotionWeaver's canonical, backend-agnostic motion contract.
It describes **parts, joints, controls, clips, and assumptions** — never Blender
or engine code.

- JSON Schema: [`schemas/motion_spec.schema.json`](../schemas/motion_spec.schema.json)
- Pydantic model: `mw_core.motion_spec.models.MotionSpec`
- Worked example: [`examples/antenna_motion_spec.json`](../examples/antenna_motion_spec.json)

## Top-level fields

| Field               | Required | Meaning                                                  |
| ------------------- | -------- | -------------------------------------------------------- |
| `schema_version`    | yes      | Spec version string.                                     |
| `asset_id`          | yes      | Stable id for the asset.                                 |
| `coordinate_system` | yes      | `up_axis`, `forward_axis`, `unit_scale_meters`.          |
| `parts`             | yes      | Movable/static parts with a geometry `selector`.         |
| `joints`            | yes      | Parent→child joints with pivot, axis, optional limits.   |
| `controls`          | yes      | Named handles driving a joint property.                  |
| `clips`             | yes      | Keyframed animations over controls.                      |
| `source_mesh`       | no       | Provenance for the imported mesh.                        |
| `assumptions`       | no       | Explicit uncertainty recorded by the parser/human.       |

## Joint vocabulary

Fixed enum: `hinge`, `slider`, `spin`, `yaw_pitch`. Angular joints
(`hinge`/`spin`/`yaw_pitch`) use degree limits (`min_deg`/`max_deg`) and
`angle_deg` controls; `slider` uses meter limits (`min_m`/`max_m`) and
`distance_m` controls.

## Validation layers

1. **Syntactic** — Pydantic + JSON Schema (`additionalProperties: false`).
2. **Semantic** — `mw_core.motion_spec.semantic_validation`:
   - unique part/joint/control/clip ids;
   - joint part references resolve; parent ≠ child;
   - the parent→child graph is acyclic (no kinematic cycles);
   - axis vectors are non-degenerate (unit-length after normalization);
   - limits match the joint type and are ordered (`min ≤ max`);
   - controls reference existing joints with a compatible property;
   - clip channels reference existing controls; keyframe times are ordered and
     within `duration_s`.

`mw_core.normalize_spec` makes axes unit-length and defaults `yaw_pitch` stacks
before validation/compilation.
