# Development

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for environment/package management
- Node 18+ (for `mw_runtime_web`)
- Blender 4.5 LTS (for `mw_blender`; smoke-tested on 5.1)

## Python workspace

```bash
uv sync                       # create env, install workspace + dev tools
uv run pytest                 # run the test suite
uv run ruff check .           # lint
uv run ruff format --check .  # format check
uv run mypy                   # type-check (excludes mw_blender)
uv run pre-commit run --all-files
```

The uv workspace contains `mw_core` and `mw_ai`. `mw_blender` is excluded
because it imports `bpy` (only available inside Blender) and is therefore also
excluded from mypy.

## Web runtime

```bash
cd packages/mw_runtime_web
npm install
npm run typecheck
npm run build
```

## Blender add-on

Zip `packages/mw_blender/mw_blender/` and install it via
*Edit > Preferences > Add-ons > Install*, or symlink the folder into Blender's
`scripts/addons`. Headless regression tests are wired in
`.github/workflows/blender-headless.yaml` (currently a placeholder).

## What is implemented vs stubbed

Implemented and tested: the `motion_spec` model, normalization, semantic
validation, the part graph, the kinematic-graph planner, and the sidecar
manifest round-trip.

TODO-backed stubs (raise `NotImplementedError`): mesh import, pivot inference,
clip baking, glTF/blend export, the AI parser providers, the Blender operators,
and the runtime adapter bindings. Each stub documents its intended
implementation inline.
