# Architecture

MotionWeaver is a **spec-first, compiler-first** system. The AI proposes
structure; deterministic code owns everything that must be correct.

```
human intent ──▶ mw_ai (parser) ──▶ motion_spec (JSON)
                                        │  validate (mw_core)
                                        ▼
                              kinematic graph (mw_core.rig)
                                        │
              ┌─────────────────────────┼──────────────────────────┐
              ▼                         ▼                          ▼
      mw_blender preview rig      baker → TRS tracks         sidecar manifest
                                        │                          │
                                        ▼                          │
                                   GLB export ◀────────────────────┘
                                        │
                          ┌─────────────┴─────────────┐
                          ▼                           ▼
                 mw_runtime_web (Three.js)    mw_runtime_unity (glTFast)
```

## Package boundaries

- **mw_core** — canonical `motion_spec` model, semantic validation,
  normalization, geometry analysis, kinematic graph, baker, exporters. No cloud
  AI, no Blender.
- **mw_ai** — provider-agnostic structured-output parser + deterministic repair.
  Emits JSON only; no execution authority.
- **mw_blender** — Blender add-on (UX). Consumes the kinematic graph; preview
  controls are authoring conveniences, classified preview-only.
- **mw_runtime_web** — Three.js reference runtime adapter.
- **mw_runtime_unity** — Unity adapter (placeholder).

## Why these boundaries

The kinematic graph is the canonical runtime representation and lives outside
every backend. Backends are compiled *from* it, never the reverse. This is what
lets the same validated spec target Blender, the web, and game engines without
semantic drift, and it keeps brittle AI logic away from execution.

See `deep-research-report.md` for the full rationale and alternatives considered.
