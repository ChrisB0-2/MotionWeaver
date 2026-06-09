# MotionWeaver

An AI-assisted **motion compiler** for rigid, multipart mechanical 3D assets
(antennas, turrets, robot arms, doors, hatches).

MotionWeaver converts human-written movement intent into a validated
`motion_spec` JSON, then **deterministically** compiles that spec into Blender
rigs, preview controls, and exportable runtime data (GLB + sidecar manifest).

It is **not** a general auto-rigger and **not** a character / deformable-mesh
rigging tool.

## Pipeline

```
human intent → AI parser → validated motion_spec → deterministic kinematic graph
            → Blender rig + preview controls → bake → GLB + sidecar manifest
            → Three.js / Unity runtime adapters
```

The AI only *parses intent and proposes structure*. Deterministic code owns mesh
analysis, pivot placement, graph construction, validation, baking, and export.
See `CLAUDE.md` for the non-negotiable design constraints and
`deep-research-report.md` for the full design study.

## Packages

| Package             | Language   | Role                                                       |
| ------------------- | ---------- | ---------------------------------------------------------- |
| `mw_core`           | Python     | Compiler core: `motion_spec`, geometry, rig, exporters     |
| `mw_ai`             | Python     | Structured-output LLM parser, prompts, repair (no exec)    |
| `mw_blender`        | Python     | Blender add-on (preview UX; not pip-installable)           |
| `mw_runtime_web`    | TypeScript | Three.js reference runtime adapter                         |
| `mw_runtime_unity`  | C#         | Unity adapter (placeholder)                                |

## Development

This project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync                 # create env + install workspace and dev tools
uv run pytest           # run tests
uv run ruff check .     # lint
uv run mypy             # type-check
uv run pre-commit run --all-files
```

`mw_blender` is **not** part of the uv workspace because it imports `bpy`, which
is only available inside Blender. Target baseline is **Blender 4.5 LTS**
(smoke-tested on 5.1).

## Status

Early scaffold. The `motion_spec` models and semantic validators are implemented;
geometry analysis, rig building, baking, export, the AI parser, and the runtime
adapters are TODO-backed stubs.
