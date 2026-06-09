"""Axis utilities: cardinal-axis conversion and local/world disambiguation."""

from __future__ import annotations

Vec3 = tuple[float, float, float]

# Map the six signed cardinal axis labels to unit vectors.
_CARDINAL: dict[str, Vec3] = {
    "X": (1.0, 0.0, 0.0),
    "-X": (-1.0, 0.0, 0.0),
    "Y": (0.0, 1.0, 0.0),
    "-Y": (0.0, -1.0, 0.0),
    "Z": (0.0, 0.0, 1.0),
    "-Z": (0.0, 0.0, -1.0),
}


def cardinal_to_vector(label: str) -> Vec3:
    """Convert a signed cardinal axis label (e.g. ``"-Z"``) to a unit vector."""
    try:
        return _CARDINAL[label]
    except KeyError as exc:
        raise ValueError(f"unknown cardinal axis label: {label!r}") from exc
