# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

This repository is **pre-implementation**. The only artifact is `deep-research-report.md`, a feasibility and design study. There is no code, build system, tests, or dependency manifest yet, and the directory is not a git repository. Treat the research report as the authoritative spec for what to build; do not assume any commands or files below exist until they are created.

## What MotionWeaver is

An **AI-assisted motion compiler for rigid, multipart mechanical 3D assets** (antennas, turrets, robot arms, doors, hatches). It converts human-written movement intent into a validated `motion_spec` JSON, then deterministically compiles that spec into Blender rigs, preview controls, and exportable runtime data (GLB + sidecar JSON).

It is explicitly **not** a general auto-rigger and **not** a character/deformable-mesh rigging tool.

## Non-negotiable design constraints

These constraints are the core of the product thesis. Violating them defeats the reason the project is feasible:

1. **Spec-first, compiler-first.** The flow is: human intent → validated `motion_spec` → deterministic kinematic graph → Blender rig → exportable asset. The LLM only parses intent and proposes structure; deterministic code owns mesh analysis, pivot placement, graph construction, validation, baking, and export.
2. **Never execute model-generated Python inside Blender as the source of truth.** The LLM emits schema-constrained JSON only. The compiler interprets that JSON through an allowlisted vocabulary of operations. This is the single most important safety/reliability rule.
3. **The canonical kinematic graph and `motion_spec` live outside Blender.** Blender drivers/constraints are preview-only authoring conveniences. Export must **bake** motion into glTF node TRS tracks; semantics go in the sidecar manifest (optionally mirrored into glTF `extras`).
4. **Joint vocabulary is a small, testable enum:** `hinge`, `slider`, `spin`, `yaw_pitch`. Do not invent joint types.
5. **Be assistive, not magic.** Make uncertainty explicit (pivot/axis/part-boundary ambiguity) and require human confirmation rather than pretending certainty. Fully automatic rigging is brittle on welded/messy meshes.
6. **The deterministic core must not depend on cloud AI.** The AI parser is an optional package.

## Planned architecture

Compiler owns a rig-agnostic kinematic graph, then compiles it into multiple backends. Package boundaries (monorepo):

- `mw_core` — Python compiler: `motion_spec` models/validation/normalization, geometry (importers, part graph, pivots, axes), rig (kinematic graph, planner, baker), exporters (gltf, blend, manifest).
- `mw_ai` — structured-output LLM parser, prompts, spec repair, parser eval cases. No execution authority.
- `mw_blender` — Blender add-on (operators, panels, properties, preview rig, import/build/bake-export). UX lives here; brittle AI logic does not.
- `mw_runtime_web` — TypeScript + Three.js adapter (GLTFLoader + AnimationMixer). This is the **reference runtime**.
- `mw_runtime_unity` — C# + glTFast adapter (second target, kept thin).

The `motion_spec` is backend-agnostic and describes **parts, joints, controls, clips, and assumptions** — never Blender or engine code. The schema sketch and a worked `antenna_motion_spec.json` example are in `deep-research-report.md`.

## Planned tech stack and tooling

When scaffolding, use these choices (from the report). None are installed yet.

- Python managed with **uv**; FastAPI for the local sidecar service.
- **Pydantic** models + **jsonschema** for validation (syntactic schema + semantic validators).
- Geometry: Blender `bpy`/`bmesh`, plus `trimesh` and `Open3D` (both MIT). Keep `PyMeshLab` (GPL) optional only, isolated from the core dependency path.
- Optional vision assist: Florence-2, Grounding DINO, SAM 2 (used only where deterministic geometry is insufficient).
- Tests/quality: **pytest**, **Ruff**, **mypy**, **pre-commit**, GitHub Actions CI (including a headless-Blender regression workflow).
- Blender baseline **4.5 LTS**, smoke-test **5.1**.
- Default LLM parser: **Claude Sonnet** family via structured outputs; GPT-4.1 / GPT-4.1 mini and Gemini 2.5 Pro as alternatives.

Expected commands once scaffolded (verify against the actual project config before relying on them): `uv sync`, `uv run pytest`, `uv run ruff check`, `uv run mypy`.

## Validation requirements

Semantic validators the core must enforce on every `motion_spec`: no part cycles; all joint part references resolve; axis vectors normalized; hinge/slider limits sane; controls reference existing joints; clip channels reference existing controls; local/world-space disambiguation; and classification of features as **preview-only vs exportable/bakeable**.
