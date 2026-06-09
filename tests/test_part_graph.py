"""Dependency-free part graph behavior."""

from __future__ import annotations

import pytest
from mw_core.geometry.part_graph import Part, PartGraph


def _graph() -> PartGraph:
    g = PartGraph()
    for pid in ("base", "mast", "dish", "hatch"):
        g.add_part(Part(id=pid))
    g.add_adjacency("base", "mast")
    g.add_adjacency("mast", "dish")
    return g


def test_neighbors_are_symmetric() -> None:
    g = _graph()
    assert "mast" in g.neighbors("base")
    assert "base" in g.neighbors("mast")


def test_connected_components_split_isolated_parts() -> None:
    g = _graph()
    comps = g.connected_components()
    sizes = sorted(len(c) for c in comps)
    # base-mast-dish form one component; hatch is isolated.
    assert sizes == [1, 3]


def test_duplicate_part_id_rejected() -> None:
    g = PartGraph()
    g.add_part(Part(id="x"))
    with pytest.raises(ValueError):
        g.add_part(Part(id="x"))


def test_self_adjacency_rejected() -> None:
    g = PartGraph()
    g.add_part(Part(id="x"))
    with pytest.raises(ValueError):
        g.add_adjacency("x", "x")
