"""Provider-agnostic spec parser.

A ``SpecParser`` takes human movement intent plus a geometry summary and returns
a candidate ``motion_spec`` (validated through ``mw_core``) together with the
model's stated assumptions and confidence. Concrete providers (Anthropic,
OpenAI, Gemini) implement :meth:`SpecParser._complete_json` using their
structured-output / tool-use APIs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from mw_core import MotionSpec, semantic_issues


@dataclass
class ParseResult:
    spec: MotionSpec | None
    raw_json: dict[str, Any]
    assumptions: list[str] = field(default_factory=list)
    # Semantic issues found in the proposal; non-empty means the proposal needs
    # repair or human confirmation before compilation.
    issues: list[str] = field(default_factory=list)


class SpecParser(ABC):
    """Base class for structured-output spec parsers."""

    @abstractmethod
    def _complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Call the provider with schema-constrained output and return parsed JSON.

        TODO: implement per provider using guaranteed-schema structured outputs
        / tool use. Must NOT request or accept executable code of any kind.
        """

    def parse(self, intent: str, geometry_summary: dict[str, Any]) -> ParseResult:
        """Produce a validated motion_spec proposal from human intent.

        TODO: build the prompt from mw_ai.prompts, call ``_complete_json`` with the
        motion_spec JSON Schema, validate into a MotionSpec, and collect semantic
        issues for the repair loop. This default implementation is a stub.
        """
        raise NotImplementedError("SpecParser.parse is not implemented yet")

    @staticmethod
    def _evaluate(raw_json: dict[str, Any]) -> ParseResult:
        """Validate raw provider JSON into a ParseResult (shared by providers)."""
        try:
            spec = MotionSpec.model_validate(raw_json)
        except Exception:  # noqa: BLE001 - surfaced as a structural issue
            return ParseResult(
                spec=None, raw_json=raw_json, issues=["proposal failed schema validation"]
            )
        return ParseResult(
            spec=spec,
            raw_json=raw_json,
            assumptions=list(spec.assumptions),
            issues=semantic_issues(spec),
        )
