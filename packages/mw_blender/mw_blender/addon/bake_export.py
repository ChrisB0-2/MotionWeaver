"""Bake clips to TRS tracks and export GLB + sidecar manifest.

TODO: use mw_core.rig.baker to bake control-driven motion into node TRS tracks,
export GLB via Blender's glTF exporter, and write the canonical sidecar manifest
via mw_core.exporters.manifest_export. Mirror stable ids into glTF extras only.
"""

from __future__ import annotations


def run(context: object) -> None:
    raise NotImplementedError("bake & export operator not implemented yet")
