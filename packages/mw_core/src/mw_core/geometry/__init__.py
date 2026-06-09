"""Deterministic mesh import and analysis.

This subpackage turns imported geometry into a part graph and candidate pivots.
It is deterministic-first (Blender loose parts, ``trimesh`` connected
components, ``Open3D`` clustering); learned vision assist lives in ``mw_ai``.
"""

from __future__ import annotations

from mw_core.geometry.part_graph import Part as PartNode
from mw_core.geometry.part_graph import PartGraph

__all__ = ["PartGraph", "PartNode"]
