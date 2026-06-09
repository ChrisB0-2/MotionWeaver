"""Build a deterministic Blender preview rig from the kinematic graph.

TODO: parent objects to empties at joint pivots, add custom-property controls and
drivers for hinge/slider/spin/yaw_pitch, and enforce limits. These preview
controls are authoring conveniences only and must be classified preview-only so
the baker excludes them from the portable export.
"""

from __future__ import annotations


def run(context: object) -> None:
    raise NotImplementedError("preview rig builder not implemented yet")
