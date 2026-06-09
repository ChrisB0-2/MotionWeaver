"""MotionWeaver compiler core.

Public surface re-exports the motion_spec model and validation entry points so
callers can ``from mw_core import MotionSpec, validate_spec``.
"""

from __future__ import annotations

from mw_core.motion_spec import (
    MotionSpec,
    SemanticError,
    normalize_spec,
    semantic_issues,
    validate_spec,
)

__all__ = [
    "MotionSpec",
    "SemanticError",
    "normalize_spec",
    "semantic_issues",
    "validate_spec",
]

__version__ = "0.1.0"
