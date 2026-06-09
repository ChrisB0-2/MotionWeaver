"""Pivot and hinge-axis candidate inference.

Pivot/axis placement is the single biggest ambiguity in mechanical motion, so
this module proposes *candidates with confidence* rather than committing. The
human (or AI proposal + human confirmation) resolves the final choice.
"""

from __future__ import annotations

from dataclasses import dataclass

Vec3 = tuple[float, float, float]


@dataclass
class PivotCandidate:
    """A proposed pivot with axis and a confidence in [0, 1]."""

    position: Vec3
    axis: Vec3
    confidence: float
    rationale: str


def pivot_candidates_from_contact(parent_mesh: object, child_mesh: object) -> list[PivotCandidate]:
    """Propose hinge pivot candidates from the contact region between two parts.

    TODO: implement by finding the shared contact surface / nearest-points
    region between parent and child geometry, then fitting an axis (e.g. PCA of
    the contact ring). Return multiple candidates when several interpretations
    are plausible, each with explicit confidence and rationale.
    """
    raise NotImplementedError("pivot inference not implemented yet")
