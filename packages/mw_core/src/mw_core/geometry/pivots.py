"""Pivot and hinge-axis candidate inference.

Pivot/axis placement is the single biggest ambiguity in mechanical motion, so
this module proposes *candidates with confidence* rather than committing. The
human (or AI proposal + human confirmation) resolves the final choice.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import trimesh

Vec3 = tuple[float, float, float]

# Contact tolerance as a fraction of the two parts' combined AABB diagonal,
# used when the caller passes no absolute ``tolerance``. Loose enough to absorb
# float noise in touching parts, tight enough not to bridge real modeled gaps.
_DEFAULT_TOLERANCE_RATIO = 0.005

# Confidence is clamped to this range: never 0.0 (every returned candidate has
# *some* geometric evidence) and never 1.0 (a pivot is never certain — the
# human confirms; see the module docstring).
_MIN_CONFIDENCE = 0.05
_MAX_CONFIDENCE = 0.9

# Confidence for the position-only "point contact" case: the pivot location is
# trustworthy but the axis is a guess, so it sits just above the floor.
_POINT_CONTACT_CONFIDENCE = 0.1


@dataclass
class PivotCandidate:
    """A proposed pivot with axis and a confidence in [0, 1]."""

    position: Vec3
    axis: Vec3
    confidence: float
    rationale: str


def pivot_candidates_from_contact(
    parent_mesh: trimesh.Trimesh,
    child_mesh: trimesh.Trimesh,
    *,
    tolerance: float | None = None,
) -> list[PivotCandidate]:
    """Propose pivot/axis candidates from the contact region between two parts.

    Collects the vertices of each part lying within ``tolerance`` of the other
    part's surface, then classifies that contact region by the spectrum of its
    principal components (SVD of the centered points):

    - an *elongated* region (hinge knuckle line, slider rail) yields a
      candidate whose axis runs along the region's long direction;
    - a *planar* region (turntable face, sleeve rim) yields a candidate whose
      axis is the contact-plane normal;
    - a *point-like* region pins the pivot position but leaves the axis a
      low-confidence guess (the parent-to-child direction).

    When several interpretations are geometrically plausible they are all
    returned, ranked by descending confidence — choosing is the human's job.
    Joint *type* is intentionally not decided here: the same elongated contact
    serves both a hinge and a slider reading of the motion intent.

    Positions and axes are in the meshes' shared (world) coordinate frame.
    Axis *sign* for SVD-derived candidates is a deterministic convention (the
    largest-magnitude component is made positive); callers must treat sign as
    user-flippable, e.g. via one-click inversion in the preview UI.

    Args:
        parent_mesh: the part the joint anchors to (a ``trimesh.Trimesh``).
        child_mesh: the part that moves relative to the parent.
        tolerance: absolute contact distance. Defaults to 0.5% of the combined
            bounding-box diagonal, which absorbs small modeled clearances.

    Returns:
        Candidates sorted by descending confidence, or ``[]`` when no contact
        region exists within tolerance (the honest "no idea" answer).

    Raises:
        TypeError: if either input is not a single mesh (Scenes must be split
            into parts first — see ``split_connected_components``).
        ValueError: if ``tolerance`` is given and not positive.
        ImportError: without the optional ``geometry`` extra installed.
    """
    try:
        import numpy as np
        import trimesh.proximity  # noqa: F401  (availability check; used in helper)
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            "pivot_candidates_from_contact requires the optional 'geometry' extra "
            "(pip install mw-core[geometry])"
        ) from exc

    for mesh in (parent_mesh, child_mesh):
        if not (hasattr(mesh, "vertices") and hasattr(mesh, "faces")):
            raise TypeError(
                "expected single trimesh.Trimesh parts (split a Scene into parts "
                f"first), got {type(mesh).__name__}"
            )
    if tolerance is not None and tolerance <= 0.0:
        raise ValueError(f"tolerance must be positive, got {tolerance}")

    parent_vertices = np.asarray(parent_mesh.vertices, dtype=float)
    child_vertices = np.asarray(child_mesh.vertices, dtype=float)
    diagonal = _union_bbox_diagonal(parent_vertices, child_vertices)
    tol = tolerance if tolerance is not None else _DEFAULT_TOLERANCE_RATIO * diagonal

    contact = np.vstack(
        [
            _vertices_near_surface(child_vertices, parent_mesh, tol),
            _vertices_near_surface(parent_vertices, child_mesh, tol),
        ]
    )
    if len(contact) == 0:
        return []

    centroid = contact.mean(axis=0)
    position = _as_vec3(centroid)
    (s1, s2, s3), directions = _principal_directions(contact - centroid)
    # Scale-relative "effectively zero" threshold for singular values.
    eps = 1e-9 * diagonal

    if s1 <= eps:
        # All contact points coincide: position is trustworthy, axis is not.
        return [
            PivotCandidate(
                position=position,
                axis=_direction_between(parent_vertices, child_vertices),
                confidence=_POINT_CONTACT_CONFIDENCE,
                rationale=(
                    f"point contact ({len(contact)} coincident contact points): pivot "
                    "position is well-defined but the axis is ambiguous; axis points "
                    "from parent toward child as a starting guess"
                ),
            )
        ]

    # 1.0 = perfectly linear region, 0.0 = isotropic in its top two directions.
    elongation = 1.0 - (s2 / s1)
    candidates = [
        PivotCandidate(
            position=position,
            axis=_canonical_sign(directions[0]),
            confidence=_scaled_confidence(elongation),
            rationale=(
                f"contact region of {len(contact)} points; axis along its longest "
                f"direction (elongation {elongation:.2f}) — hinge/slider-style line"
            ),
        )
    ]
    if s2 > eps:
        # The region genuinely spans a plane, so its normal is a second
        # plausible axis — strongest when the region is flat and not elongated
        # (a disc or ring), e.g. a turret ring or a cylinder rim.
        flatness = 1.0 - (s3 / s2)
        candidates.append(
            PivotCandidate(
                position=position,
                axis=_canonical_sign(directions[2]),
                confidence=_scaled_confidence(flatness * (1.0 - elongation)),
                rationale=(
                    f"planar contact region of {len(contact)} points; axis along the "
                    f"contact-plane normal (flatness {flatness:.2f}) — spin/turntable-style"
                ),
            )
        )

    candidates.sort(key=lambda candidate: candidate.confidence, reverse=True)
    return candidates


def _vertices_near_surface(points: Any, target_mesh: Any, tol: float) -> Any:
    """Return the subset of ``points`` within ``tol`` of ``target_mesh``'s surface."""
    import trimesh.proximity

    if len(points) == 0:
        return points
    query = trimesh.proximity.ProximityQuery(target_mesh)
    _, distances, _ = query.on_surface(points)
    return points[distances <= tol]


def _principal_directions(centered: Any) -> tuple[Vec3, Any]:
    """SVD of centered points: singular values (padded to 3) + direction rows.

    With fewer than three points numpy returns fewer than three singular
    values; missing ones are zero by definition. Row ``i`` of the returned
    directions matrix only exists for each nonzero singular value, which is
    exactly when callers may index it.
    """
    import numpy as np

    _, singular_values, vt = np.linalg.svd(centered, full_matrices=False)
    padded = [float(s) for s in singular_values] + [0.0] * (3 - len(singular_values))
    return (padded[0], padded[1], padded[2]), vt


def _union_bbox_diagonal(parent_vertices: Any, child_vertices: Any) -> float:
    """Diagonal of the AABB enclosing both vertex sets (0.0 when empty)."""
    import numpy as np

    stacked = np.vstack([parent_vertices, child_vertices])
    if len(stacked) == 0:
        return 0.0
    return float(np.linalg.norm(stacked.max(axis=0) - stacked.min(axis=0)))


def _direction_between(parent_vertices: Any, child_vertices: Any) -> Vec3:
    """Unit vector from the parent's vertex centroid toward the child's.

    Falls back to +Z when the centroids coincide. Unlike SVD axes this keeps
    its semantic sign (parent -> child), so it is not sign-canonicalized.
    """
    import numpy as np

    vec = child_vertices.mean(axis=0) - parent_vertices.mean(axis=0)
    norm = float(np.linalg.norm(vec))
    if norm <= 0.0:
        return (0.0, 0.0, 1.0)
    return _as_vec3(vec / norm)


def _canonical_sign(direction: Any) -> Vec3:
    """Normalize and flip ``direction`` so its largest-|component| is positive.

    SVD direction signs are arbitrary; this makes them deterministic. The
    *mechanically* correct sign is the user's call (one-click inversion).
    """
    import numpy as np

    vec = np.asarray(direction, dtype=float)
    vec = vec / np.linalg.norm(vec)
    if vec[int(np.argmax(np.abs(vec)))] < 0.0:
        vec = -vec
    return _as_vec3(vec)


def _scaled_confidence(evidence: float) -> float:
    """Map evidence in [0, 1] onto the [floor, ceiling] confidence band."""
    clamped = min(max(evidence, 0.0), 1.0)
    return _MIN_CONFIDENCE + (_MAX_CONFIDENCE - _MIN_CONFIDENCE) * clamped


def _as_vec3(values: Any) -> Vec3:
    x, y, z = (float(v) for v in values)
    return (x, y, z)
