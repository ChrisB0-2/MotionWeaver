"""Prompt scaffolds for the spec parser.

Prompts must constrain the model to emit a ``motion_spec`` JSON object only and
to express uncertainty as explicit assumptions rather than guessing. The model
is never asked for Blender or engine code.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are MotionWeaver's motion parser. You convert human movement instructions \
about a rigid, multipart MECHANICAL 3D asset into a motion_spec JSON object.

Rules:
- Output a single motion_spec JSON object that conforms to the provided schema. \
Output nothing else.
- Joint types are limited to: hinge, slider, spin, yaw_pitch. Never invent types.
- Assume rigid mechanical motion only. No skinning, no deformation, no humanoid \
skeletons.
- Prefer conservative structure. When a pivot, axis, or part boundary is \
ambiguous, record it in "assumptions" rather than guessing confidently.
- Never produce Blender Python, engine code, or any executable content.
"""


def build_user_prompt(intent: str, geometry_summary: str) -> str:
    """Assemble the user-facing prompt from intent and a geometry summary.

    TODO: include few-shot exemplars (e.g. the antenna example) and the part
    graph / candidate pivots so the model grounds joints in real geometry.
    """
    return (
        "Movement intent:\n"
        f"{intent}\n\n"
        "Geometry summary (parts, names, candidate pivots):\n"
        f"{geometry_summary}\n"
    )
