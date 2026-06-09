"""Deterministic repair of nearly-valid spec proposals.

When a parsed proposal has semantic issues, prefer cheap deterministic fixes
(e.g. re-normalizing axes) over another model round-trip. Issues that require
real geometric judgement are returned for human confirmation, never silently
guessed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mw_core import MotionSpec, normalize_spec, semantic_issues


@dataclass
class RepairResult:
    spec: MotionSpec
    applied: list[str] = field(default_factory=list)
    remaining_issues: list[str] = field(default_factory=list)


def repair(spec: MotionSpec) -> RepairResult:
    """Apply safe deterministic repairs and report what remains.

    Currently applies axis normalization (and yaw_pitch stack defaults) via
    ``normalize_spec``. TODO: add limit clamping and pivot-space coercion where
    unambiguous; escalate the rest to human confirmation.
    """
    applied: list[str] = []
    try:
        repaired = normalize_spec(spec)
        applied.append("normalized joint axes")
    except ValueError:
        # A degenerate axis cannot be auto-repaired; leave it for validation.
        repaired = spec
    return RepairResult(
        spec=repaired,
        applied=applied,
        remaining_issues=semantic_issues(repaired),
    )
