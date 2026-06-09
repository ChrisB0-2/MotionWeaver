"""MotionWeaver AI parser package.

Provider-agnostic interface that produces schema-constrained ``motion_spec``
proposals. Emits JSON only; never executes code.
"""

from __future__ import annotations

from mw_ai.parser import ParseResult, SpecParser

__all__ = ["ParseResult", "SpecParser"]
