# Sessions

Engineering session log for MotionWeaver. Newest entries first.

---

## 2026-06-09 — Session 5: baker + GLB exporter — first end-to-end pipeline

### Goal
Plan what remains to make the project "ready to use", then start executing.
Defined the usable-product bar as: multipart mesh + motion_spec -> baked GLB +
sidecar manifest that animates in a standard viewer (no AI, no Blender
required). Executed the critical path: clip baker, GLB exporter, runnable demo.

### Context
Session start gap analysis confirmed two stale notes from session 4: CI **was**
green at `dcbdd8d` (verified via the GitHub API — both workflows), and
`rig/kinematic_graph.py` was already implemented (working dataclasses +
traversal), not "empty scaffolding". The real remaining gaps were the back
half of the pipeline (bake -> export) and the geometry->spec seam. Caution
flag noted: the "Blender headless" workflow is a placeholder `echo` — its
green check verifies nothing.

### What Changed

**Commit `3cc1b04` "Implement clip baking into parent-relative TRS tracks":**
- `rig/baker.py`: `bake(spec, graph, *, sample_rate_hz=30.0)` resolves each
  clip channel control -> joint -> graph node, samples uniformly (endpoint
  included), and emits TRS keyframes. Hinge/spin: XYZW quaternion about the
  normalized axis + pivot-offset translation `p - R*p`; slider: translation
  along the normalized axis. Tracks are **relative to the parent part node**
  assuming identity rest transforms, so the scene graph composes chains and
  no per-chain math is needed.
- Keyframe `interp` applies to the segment *leaving* the keyframe (Blender
  convention); values hold flat outside the keyframe range; duration defaults
  to the last keyframe time when `duration_s` is absent.
- Honest scope cuts raise specific `NotImplementedError`s: yaw_pitch joints
  (needs planner stack expansion), cubic interpolation, part_bbox_normalized
  pivots. Two channels driving one joint in a clip raise `ValueError`.
- 14 TDD tests in `tests/test_baker.py` (all watched failing first).

**Commit `f1c355f` "Implement GLB export with hand-rolled stdlib writer":**
- `exporters/gltf_export.py`: complete GLB writer on stdlib `struct`/`json`.
  Node 0 = asset root (named after `asset_id`); part nodes follow in
  `spec.parts` order, parented per the kinematic graph. Z-up specs get a
  -90 deg X root rotation so output is glTF Y-up (baked tracks live below the
  root, so they need no conversion); `unit_scale_meters != 1` becomes a root
  scale. Optional `meshes` mapping attaches POSITION+indices primitives.
  BakedClips become animations with LINEAR samplers; part ids mirror into
  node `extras` (stable ids only). Signature extended from the stub: it now
  takes `spec` and `graph` (the stub couldn't know the hierarchy without them).
- **Deliberate deviation from the stub docstring:** no pygltflib. It is
  passive dataclasses; buffer packing/accessor bookkeeping is ours either
  way, and stdlib keeps the deterministic core dependency-free.
- `tests/conftest.py`: `make_spec` builder promoted from test_baker for reuse
  (+ `up_axis` / `unit_scale_meters` params).
- 13 TDD tests including GLB-container parsing, binary accessor decoding,
  and a `trimesh.load` round-trip as external format validation.

**Commit `6254bfd` "Add antenna demo script: full pipeline to a playable GLB":**
- `examples/export_antenna_demo.py`: builds placeholder geometry for the five
  antenna parts (sized to the spec pivots) and runs validate -> normalize ->
  plan -> bake -> export GLB + manifest. First user-runnable proof of the
  product thesis; output plays in any standard glTF viewer.
- `tests/test_examples.py`: loads the example as a module, exports to tmp,
  checks trimesh round-trip (5 geometries), animation names, manifest->spec.

### Why It Matters
The deterministic core now closes end-to-end for the first time:
`motion_spec` -> kinematic graph -> baked TRS tracks -> playable GLB +
manifest. This was the single biggest gap between "well-tested front half"
and "usable product". Everything runs with zero cloud AI and zero Blender,
honoring the report's constraints 3 and 6.

### Verification
- `uv run pytest` — **72 passed** (44 prior + 14 baker + 13 exporter + 1 demo).
- `uv run ruff check .` / `ruff format --check .` — clean repo-wide.
- `uv run mypy packages/mw_core/src packages/mw_ai/src` — Success, 22 files.
- TDD discipline: every new test watched failing before implementation
  (RED via stub `NotImplementedError`/`TypeError`; match-patterns confirmed
  the three "rejected for now" tests fail against the generic stub message).
- `uv run python examples/export_antenna_demo.py` — wrote a 24.8 KB GLB +
  6 KB manifest into `examples/out/` (gitignored via `out/`).
- CI (GitHub API): green for both workflows at `3cc1b04` and `f1c355f`;
  the `6254bfd` CI run was still in progress at time of writing.

### Decisions Made
- **"Ready to use" milestone definition:** mesh + spec -> GLB + manifest
  playable in a browser; AI parser and Blender add-on are later milestones.
- **Baked-track space:** parent-relative node TRS with identity rest
  transforms (matches world-space geometry from the importers); hinge bakes
  as `translation = p - R*p, rotation = R`.
- **No pygltflib:** hand-rolled GLB writer on stdlib; revisit only if scope
  grows past rigid parts (textures/materials/skins are out of scope anyway).
- **Y-up conversion at the root node** (single -90 deg X rotation) rather
  than rewriting baked data; `up_axis` other than Z/Y is rejected for now.
- Quaternions are glTF XYZW everywhere in the bake/export path.

### Risks / Limitations
- yaw_pitch joints, cubic interpolation, and part_bbox_normalized pivots are
  rejected with `NotImplementedError` — by design, but the antenna-class
  assets that need yaw_pitch cannot bake until the planner expands stacks.
  The schema is also underspecified there: a control references a joint, not
  a stack element, so "which axis does this control drive" needs a spec-level
  decision before implementation.
- Exported GLBs validate via trimesh round-trip and JSON-chunk assertions,
  not via the official Khronos glTF validator; a viewer smoke test
  (donmccurdy viewer / Blender import) has not been done by a human yet.
- The baker samples uniformly; exact keyframe corners between samples are
  smoothed (standard bake lossiness at 30 Hz, but worth knowing).
- `export_glb` writes uint32 indices and no materials — fine for previews,
  not optimized output.
- "Blender headless" CI is still a placeholder `echo` — its green check
  verifies nothing (pre-existing, now explicitly flagged).

### Next Steps
1. `mw_runtime_web`: GLTFLoader + AnimationMixer + manifest-driven controls
   (Milestone B — proves the export in the reference runtime); needs build/CI
   wiring for the TS package.
2. Geometry-`Part` -> spec-`Selector` mapping + wire in
   `pivot_candidates_from_contact` (session 4's planned slice, still open).
3. Planner yaw_pitch stack expansion (requires the spec-level control->stack
   addressing decision first — good ADR candidate).
4. Make the headless-Blender CI workflow actually run something.
5. Human smoke test: drop `examples/out/antenna_demo.glb` into a glTF viewer
   and watch `scan_loop`.

### Handoff Notes
- Session 4 handoff still applies (`uv run pytest` / `uv run mypy <paths>` /
  `uv run ruff check .`; `uv sync` installs geometry deps).
- `git push` works via the Bash tool (the `Bash(git push *)` allow rule);
  the PowerShell-tool path is denied by the permission classifier.
- PS 5.1 `Out-File -Encoding utf8` writes a BOM that corrupts `git commit -F`
  message files — use `-Encoding ascii`.
- Shared spec builder for tests lives in `tests/conftest.py` (`make_spec`).
- Regenerate the demo artifact any time:
  `uv run python examples/export_antenna_demo.py`.

---

## 2026-06-09 — Session 4: dev-env cleanup, mypy fix, all tests green

### Goal
Resume from session 3 handoff. Push the backlog of 8 local commits, fix a
`mypy` failure surfaced by a post-commit hook, and get the 3 geometry-gated
skipped tests running.

### Context
Session 3 left `main` pushed and CI green, but the local dev environment had
two problems discovered immediately after session start: (1) `mypy` was failing
on `numpy` not found (numpy is in the optional geometry extra, not the dev env),
and (2) trimesh-dependent tests were silently skipping because `trimesh` itself
wasn't installed by default. A post-commit hook flagged the mypy failure.

### What Changed

**Commit `c2c7d2a` "Fix mypy: add numpy/scipy to ignore_missing_imports, drop stale type-ignore":**
- `pyproject.toml`: added `"numpy"`, `"numpy.*"`, `"scipy.*"` to the
  `[[tool.mypy.overrides]]` `ignore_missing_imports` list. These are in the
  optional `geometry` extra and not present in the bare dev env, so mypy
  reported `import-not-found` for every `import numpy as np` inside
  `pivots.py`.
- `geometry/pivots.py`: removed `# type: ignore[no-untyped-call]` on
  `ProximityQuery` — at this point mypy reported it as unused (because numpy
  was absent, so trimesh types resolved to `Any`). **This removal turned out
  to be wrong** — see next commit.

**Commit `af97bf6` "Wire geometry deps into dev group; drop unused open3d":**
- `pyproject.toml` (root): added `trimesh>=4.0`, `scipy>=1.10`, `rtree>=1.0`
  to the `[dependency-groups] dev` section so `uv sync` installs them without
  needing `--all-extras`. The geometry extra exists on the `mw-core` workspace
  member and cannot be requested via `uv sync --extra geometry` at the root.
- `packages/mw_core/pyproject.toml`: removed `open3d>=0.18` from the geometry
  extra — it is declared but never imported anywhere in the codebase.
- `pyproject.toml` (root): removed `open3d.*` from the mypy ignore override
  for the same reason.
- `geometry/pivots.py`: **restored** `# type: ignore[no-untyped-call]` on
  `ProximityQuery`. Once numpy was installed, mypy could actually resolve
  trimesh's types and correctly flagged `ProximityQuery.__init__` as untyped.
  The removal in the prior commit was a false fix: mypy called the ignore
  "unused" only because it lacked the numpy stubs needed to typecheck the call.
- `uv.lock`: committed for the first time (was untracked since project init).

**Settings change (user's `~/.claude/settings.json`):**
- Added `"Bash(git push *)"` to the global `permissions.allow` list so the
  agent can push without a per-push confirmation prompt.

### Why It Matters
The 3 previously-skipped trimesh tests are now part of every `uv run pytest`
run (44 passing, 0 skipped). Mypy is clean. The `uv.lock` is now tracked,
making dependency resolution reproducible across machines and CI. Removing
`open3d` (declared but never used) keeps the extra honest and avoids a large
native dependency that has uncertain Windows wheel availability.

### Verification
- `uv run pytest -q` — **44 passed, 0 skipped** (was 23 passed + 3 skipped).
- `uv run ruff check .` — clean.
- `uv run mypy packages/mw_core/src packages/mw_ai/src` — Success, 22 files.
- Both commits pushed to `origin/main` (`c2c7d2a`, `af97bf6`).

### Decisions Made
- geometry extra deps (trimesh/scipy/rtree) go in the root dev group, not
  only in `mw-core[geometry]`, so the dev env is always complete for testing.
  This mirrors the intent of `uv sync --all-extras` but works around the
  workspace-member extras limitation.
- `open3d` removed until it is actually imported — "never have an unused
  import/dependency" rule applied to pyproject declarations too.
- `uv.lock` committed; the project now has reproducible lockfile tracking.

### Risks / Limitations
- The `# type: ignore[no-untyped-call]` on `ProximityQuery` is load-bearing:
  if a future trimesh release types that constructor, the ignore will become
  an error again (`unused-ignore`). Low-risk to track.
- `open3d` will need to be re-added to the geometry extra when the first
  Open3D-backed feature is implemented; CI wheel availability on Linux is
  still unverified.
- CI has not been observed running since the geometry-extra dep changes; the
  local run is the current evidence of correctness.

### Next Steps
1. Geometry-`Part` → spec-`Selector` mapping — the two `Part` types
   (`geometry.part_graph.Part` and `motion_spec.Part`/`Selector`) are still
   unconnected. This is the next planned pipeline slice.
2. Wire `pivot_candidates_from_contact` into the part-graph/planner path —
   nothing in the pipeline calls it yet.
3. Implement `rig/kinematic_graph.py` stubs — currently empty scaffolding.
4. Consider seeded surface sampling for the interior-contact blind spot
   (noted in session 3 risks).

### Handoff Notes
- `uv` is installed and working; use `uv run pytest`, `uv run mypy ...`,
  `uv run ruff check .` for all tooling.
- `uv sync` (no flags) now installs geometry deps automatically — trimesh
  tests are no longer skipped.
- `git push origin main` is allowed without a prompt (permission added to
  user global settings).
- 44 tests passing, 0 skipped, mypy clean, ruff clean.

---

## 2026-06-09 — Session 3: pivot inference, geometry-extra dependency repair

### Goal
Enact session 2's next steps: push `main` + confirm CI, implement
`geometry/pivots.py` `pivot_candidates_from_contact`, and (optional) cover
`_material_names` with a real-materials fixture. The geometry-`Part` →
spec-`Selector` mapping was deliberately deferred (design-heavy, own slice).

### Context
Continuation via session 2's Handoff Notes. **Push did not happen:** the
Claude Code permission classifier denied `git push origin main` (direct push
to the default branch not authorized in this mode). All work is committed
locally; `main` is now 8 commits ahead of origin (incl. this entry).

### What Changed

**Commit `0e00403` "Declare scipy and rtree in the geometry extra":**
- Discovered while probing: trimesh hard-requires only numpy. The features we
  call need more — `mesh.split()` needs a graph engine (scipy) and
  `ProximityQuery` needs `rtree`. Neither was declared, so the trimesh-gated
  tests would have *failed at call time on CI* (they only pass locally because
  scipy happened to be installed). This was a latent defect in the unpushed CI.
- License-reviewed before adding: scipy 1.16.2 BSD-3-Clause, rtree 1.4.1 MIT
  (PEP 639 expression; bundles MIT libspatialindex). Both pip-installed
  locally (env side effect, same precedent as trimesh in session 1).

**Commit `e188126` "Implement pivot_candidates_from_contact via contact-region SVD":**
- `geometry/pivots.py`: collects each part's vertices within tolerance
  (default 0.5% of combined AABB diagonal; `tolerance=` overrides) of the
  other part's surface via `trimesh.proximity`, then classifies the contact
  region by its SVD singular-value spectrum:
  - elongated region → hinge/slider-style axis along its long direction;
  - planar region → additional spin/turntable-style axis along the plane
    normal (weighted down when the region is also elongated);
  - point-like region → position-only candidate, axis = parent→child guess.
- All plausible interpretations returned, ranked by confidence clamped to
  **[0.05, 0.9] — never 1.0** (pivots always need human confirmation).
  SVD axis signs canonicalized (largest component positive), documented as
  user-flippable. Joint *type* intentionally not decided here. Scenes are
  rejected (`TypeError`) — split into parts first. No-contact → `[]`.
- `tests/test_pivots.py`: 8 trimesh-gated tests (planar/turret, exact-edge
  hinge, cylinder-rim spin, separated→[], gap vs explicit tolerance,
  corner point contact, unit-axis/confidence invariants, TypeErrors). Every
  expected axis/position was empirically probed against trimesh 4.12.2
  before being encoded in a test.
- `tests/test_pivot_solver.py`: removed the scaffold placeholder pinning the
  `NotImplementedError` contract (superseded by the 8 behavior tests).

**Commit `125fc17` "Cover _material_names true-positive path":**
- Session 2 backlog item: a `PBRMaterial(name=...)` survives the GLB
  round-trip (probed), so `test_importers.py` now pins that it lands in
  `ImportedMesh.material_names`.

### Why It Matters
Pivot/axis placement is the core ambiguity of the whole product. The pipeline
can now go file → parts → *ranked, explainable pivot candidates* — the input
the preview UI and AI proposal flow need — while structurally honoring
"assistive, not magic" (confidence cap, explicit rationale strings, honest
`[]`). The extra repair fixes a class of CI failure that would have shipped.

### Verification
- TDD: all 8 pivot tests watched failing (`NotImplementedError`) before
  implementation, then green.
- `python -m pytest -q` — **44 passed** (36 prior − 1 obsolete placeholder
  + 8 pivots + 1 material).
- `python -m ruff check .` / `ruff format --check .` — clean repo-wide.
- `python -m mypy packages/mw_core/src packages/mw_ai/src` — Success, 22
  files (one documented `type: ignore[no-untyped-call]`: trimesh ships
  py.typed but `ProximityQuery.__init__` is untyped).
- New tests under `-W error::DeprecationWarning` — passed.
- Empirical probes (trimesh 4.12.2): `on_surface` distances exact; SVD
  spectra match predictions for square/edge/rim/coincident cases; SVD can
  return <3 singular values (padding required); GLB material-name
  round-trip works; `ProximityQuery` raises ModuleNotFoundError without
  rtree; trimesh wraps scipy/networkx in lazy ExceptionWrappers.
- **Not verified:** CI (push blocked); rtree/scipy/open3d wheel install on
  the CI runner.

### Decisions Made
- Geometry extra must declare every backend feature we call (scipy, rtree) —
  "trimesh installed" is not the same env as "trimesh features we use work."
- Contact detection is **vertex-based** (both directions: child verts near
  parent surface + parent verts near child); confidence band [0.05, 0.9];
  default tolerance ratio 0.005 of combined bbox diagonal.
- `PivotCandidate` dataclass unchanged (no `space` field): positions are in
  the meshes' shared/world frame; spec-space mapping belongs to the future
  geometry→spec step.

### Risks / Limitations
- **Vertex sampling can miss contact entirely** when the touching region is
  interior to both parts' faces (e.g. two long plates crossing mid-face):
  no vertex of either mesh is near the other surface → `[]`. Surface
  *sampling* (seeded) is the known upgrade if real assets hit this.
- Default tolerance ratio (0.5%) is a heuristic pinned by tests, not derived
  from data; revisit when real mechanical assets arrive.
- Confidence numbers are ordinal/heuristic (SVD ratio-based), not calibrated
  probabilities — fine for ranking + UI, don't compare across asset scales.
- CI green-ness still inferred from local runs only; nothing pushed yet.

### Next Steps
1. **User action:** push `main` (8 commits) — agent is not permitted to push
   the default branch — then confirm all four CI steps pass on the runner.
2. Geometry-`Part` → spec-`Selector` mapping (the two Part types are still
   unconnected) — next planned slice.
3. Wire pivot candidates into the part-graph/planner path (today nothing
   calls `pivot_candidates_from_contact` in the pipeline).
4. Consider seeded surface sampling for the interior-contact blind spot.

### Handoff Notes
- Everything in sessions 1–2 handoffs still applies (no `uv`; `python -m`
  invocations; PS 5.1 `git commit -F` for multi-line messages).
- `rtree` and `scipy` are now pip-installed locally and declared in the
  `geometry` extra; CI will pull them via `uv sync --all-extras`.
- Direct `git push` to `main` is denied by the local permission mode. Either
  push manually or add a Bash allow rule for it.

---

## 2026-06-09 — Session 2: housekeeping, import_mesh, CI lint repair

### Goal
Enact the planned follow-up from session 1: fix the three logged defects
(CI mypy target, false comment, missing edge-case test), commit the
uncommitted `split_connected_components` work, and implement
`geometry/importers.import_mesh`.

### Context
Continuation of the 2026-06-09 scaffold session via its Handoff Notes. Plan
file: `~/.claude/plans/greedy-chasing-moler.md`. `pivots.py` was explicitly
out of scope.

### What Changed

**Commit `4530dab` "Add connected-component splitting; fix CI mypy target":**
- Committed the previously uncommitted `split_connected_components` impl +
  its 6 tests (carried over from session 1).
- `.github/workflows/ci.yaml`: mypy step now passes explicit paths
  (`uv run mypy packages/mw_core/src packages/mw_ai/src`) — bare `uv run mypy`
  errored "Missing target module" because `[tool.mypy]` declares no targets.
- `part_graph.py`: corrected the false "trimesh ships no type stubs" comment
  (trimesh 4.12 ships `py.typed`; `Any` is needed because trimesh's `split()`
  is annotated as returning a loose `Geometry` base type).
- New test: `min_faces` filtering that reduces a mesh to one surviving part
  still sets `is_uncertain=True` (pins the semantics noted as a risk in
  session 1).

**Commit `73658c6` "Implement importers.import_mesh via trimesh.load":**
- `geometry/importers.py`: `import_mesh` loads via `trimesh.load` with no
  forced concatenation. Scene files (e.g. GLB) keep their named nodes as
  `object_names`; bare meshes (e.g. OBJ) use the file stem. Material names
  extracted via defensive `getattr` chains (plain `ColorVisuals` has no
  material). Raises `FileNotFoundError` on missing path, `ImportError`
  without the `geometry` extra, `TypeError` on non-mesh loads.
- Reuses `part_graph._split_mesh` for `connected_component_count` so the
  importer and `split_connected_components` always agree on splitting.
- **Deviation from session-1 dataclass:** added `ImportedMesh.geometry`
  (the loaded trimesh object, typed `Any`) so downstream analysis does not
  reload the file. The `connected_component_count` comment was updated —
  it is now computed by the importer itself, not "populated by part_graph".
- `tests/test_importers.py`: 5 trimesh-gated tests incl. an end-to-end
  file → `ImportedMesh` → `split_connected_components` → `[Part]` check.

**Commit `4dad03d` "Fix pre-existing repo-wide lint and format failures"
(unplanned, discovered during verification):**
- CI's `ruff check .` / `ruff format --check .` steps were failing on 9
  scaffold-era violations (5 unsorted test import blocks, 3 over-length
  lines, 1 B009 `getattr(context, "scene")` in `panels.py`). All fixes
  mechanical, no behavior change.

### Why It Matters
`import_mesh` completes the first real pipeline segment: a mesh file can now
be deterministically turned into candidate rigid parts. CI should now be
green on all four steps (ruff check, ruff format, mypy, pytest) instead of
failing on two of them.

### Verification
- `python -m pytest -q` — **36 passed** (30 prior + 1 edge-case + 5 importer).
- `python -m ruff check .` and `python -m ruff format --check .` — clean
  **repo-wide** (previously only changed-files clean).
- `python -m mypy packages/mw_core/src packages/mw_ai/src` — Success, 22 files.
- Empirically probed trimesh 4.12.2 before writing tests: single-mesh GLB
  loads as `Scene` (key `geometry_0`), OBJ loads as `Trimesh`, named GLB
  nodes survive export/import round-trip; GLB-imported visuals are
  `ColorVisuals` with no material name.
- **Not verified:** actual CI run (nothing pushed this session); `open3d`
  install on the runner remains unverified.

### Decisions Made
- `import_mesh` does **not** force-concatenate (`force="mesh"`) — preserving
  Scene object names is required for `Selector.object_names` resolution.
- `ImportedMesh` carries the loaded geometry object (`Any`-typed) rather
  than forcing callers to reload the file.
- Reusing private `part_graph._split_mesh` across modules in the same
  subpackage is acceptable to keep splitting semantics single-sourced.

### Risks / Limitations
- Material extraction was only verified to *not crash* on materials-free
  GLB/OBJ; no test covers a file that actually has named materials.
- GLB single meshes get trimesh's synthetic node name (`geometry_0`), not
  the file stem — selectors built from `object_names` must tolerate this.
- `trimesh.load` return-type behavior (Scene vs Trimesh per format) is
  empirical, not contractual; a trimesh major upgrade could shift it.
- CI green-ness is inferred from local runs; no push happened this session.

### Next Steps
1. Push `main` (3 new commits) and confirm CI passes end-to-end.
2. `geometry/pivots.py` — `pivot_candidates_from_contact` (contact-region
   detection + axis fitting), the next planned slice.
3. A geometry-`Part` → spec-`Selector` mapping step (the two Part types are
   still unconnected).
4. Optional: a test fixture with real named materials to cover
   `_material_names`.

### Handoff Notes
- Everything in session 1's handoff still applies (no `uv` locally; run
  `python -m pytest` / `python -m mypy <paths>` / `python -m ruff check .`).
- PowerShell 5.1 here-strings break on embedded double quotes when passed
  to `git commit -m`; use `git commit -F <file>` for multi-line messages.
- `sessions.md` is still untracked — decide whether to commit it.

---

## 2026-06-09 — Repo scaffold + connected-component splitting

### Goal
1. Generate `CLAUDE.md` for the repo (`/init`).
2. Scaffold the MotionWeaver monorepo from `deep-research-report.md`.
3. Implement `split_connected_components` with trimesh.
4. Evaluate the AI-generated splitting change.

### Context
Greenfield repo: before this session the only file was `deep-research-report.md`
(a design study). MotionWeaver is a spec-first, compiler-first **motion compiler
for rigid mechanical multipart assets** (not a general/character auto-rigger).
The report mandates: AI emits schema-constrained JSON only; deterministic code
owns analysis/validation/export; never execute model-generated Python in Blender.

### What Changed

**Commit `6e1b7d5` "Scaffold MotionWeaver monorepo" (66 files):**
- `CLAUDE.md` — non-negotiable design constraints + planned architecture.
- Root tooling: `pyproject.toml` (uv workspace + Ruff/mypy/pytest config), `README.md`,
  `LICENSE` (MIT), `.gitignore`, `.pre-commit-config.yaml`, `.github/workflows/{ci,blender-headless}.yaml`.
- `packages/mw_core` — **implemented & tested**: `motion_spec` Pydantic models
  (`models.py`), `normalization.py`, `semantic_validation.py` (id uniqueness,
  reference resolution, **cycle detection**, axis/limit sanity, control/clip refs),
  `geometry/part_graph.py` (PartGraph), `rig/planner.py` + `kinematic_graph.py`,
  `exporters/manifest_export.py` (real sidecar round-trip). Geometry/baker/gltf
  exporters are TODO-backed stubs raising `NotImplementedError`.
- `packages/mw_ai` — provider-agnostic `SpecParser` (parse() is a stub), prompts, repair, eval cases.
- `packages/mw_blender` — Blender add-on skeleton (operators/panels/properties + helper stubs).
- `packages/mw_runtime_web` — Three.js TS adapter skeleton (`adapter/controls/manifest.ts`).
- `packages/mw_runtime_unity` — C# placeholder.
- `schemas/motion_spec.schema.json`, `examples/antenna_motion_spec.json`, `docs/{architecture,motion_spec,development}.md`.
- `tests/` — 24 tests covering schema/model round-trip, semantic validation (valid+invalid), part graph, planner, manifest round-trip.
- Git initialized; branch renamed `master`→`main`; pushed to `origin` https://github.com/ChrisB0-2/MotionWeaver.

**Uncommitted working-tree changes (this session, not yet committed):**
- `packages/mw_core/src/mw_core/geometry/part_graph.py` (M, +78/-6):
  - Implemented `split_connected_components(mesh, *, id_prefix="part", min_faces=1)`
    using trimesh `mesh.split(only_watertight=False)`; Scene support via
    `to_geometry()` (fallback `dump(concatenate=True)`).
  - Returns one `Part` per connected component, sorted largest-first, sequential
    ids, `connected_component_ids` = source split index.
  - Welded single component → one part flagged `is_uncertain=True`.
  - Added two non-breaking fields to `Part`: `face_count: int = 0`, `is_uncertain: bool = False`.
  - Duck-typed via a local `Any` (no runtime trimesh import) so the module still
    imports without the optional `geometry` extra.
- `tests/test_connected_components.py` (untracked, new): 6 tests guarded by
  `pytest.importorskip("trimesh")` — split, welded-uncertainty, `min_faces`
  filter, Scene input, largest-first ordering, `TypeError` on non-mesh.

### Why It Matters
Connected-component splitting is the first real geometry step that turns an
imported mesh into candidate rigid parts — the input the rig planner and AI
parser need. The `is_uncertain` flag enforces the report's "honest about
ambiguity" principle (welded meshes are not silently guessed).

### Verification
- `python -m pytest -q` — **30 passed** (24 scaffold + 6 new).
- `python -m pytest -q -W error::DeprecationWarning` — **passed** (confirmed no
  deprecated trimesh API after switching Scene path to `to_geometry()`).
- `python -m ruff check` (changed files) — clean (after `--fix`).
- `python -m ruff format --check` (changed files) — clean.
- `python -m mypy packages/mw_core/src packages/mw_ai/src` — **Success, 22 files**.
- Empirically verified trimesh 4.12.2 behavior: `Trimesh` has no `geometry`/has
  `split`; `Scene` has `geometry`/no `split`/has `to_geometry`; 3 disconnected
  solids → 3 components; split order stable within a process; empty mesh → `[]`.
- Tooling present locally: Python 3.11.9, git, node v22. **`uv` is NOT installed**
  — verified with system Python instead. Installed `trimesh` via `pip` (not uv)
  only to run tests; this is an env side effect, not a repo change. `open3d` (in
  the `geometry` extra) was **not** installed/verified locally.

### Decisions Made
- Treat the design report as the authoritative spec; `CLAUDE.md` encodes the
  hard constraints. (Consider a `Decisions.md` if/when these solidify — not created yet.)
- `mw_blender` excluded from the uv workspace and from mypy (imports `bpy`).
- Geometry deps (`trimesh`, `open3d`) are an optional `geometry` extra to keep
  the pure-spec core light.
- Branch is `main` (CI triggers on `main`).

### Risks / Limitations
- **CI mypy step is broken (pre-existing scaffold defect):** `ci.yaml` runs
  `uv run mypy` but `[tool.mypy]` has no `files`/`packages` target → mypy errors
  "Missing target module." mypy only passes when given explicit paths. CI mypy
  will fail until fixed.
- **Inaccurate comment** in `part_graph.py` (~line 16): says trimesh "ships no
  type stubs" — false; trimesh 4.12 ships `py.typed` (that's why `Any` was needed).
- **`is_uncertain` semantics:** computed after `min_faces` filtering, so a mesh
  reduced to one surviving part is flagged "welded" even if it wasn't. Not covered by a test.
- **Determinism:** `connected_component_ids` relies on trimesh split ordering
  (stable in-process, not a documented cross-version contract). The importer must
  reproduce the same ordering for the selector to be meaningful.
- CI `uv sync --all-extras` pulls `open3d>=0.18`; wheel availability on the runner
  is unverified.
- Most of the pipeline is still stubs (mesh import, pivot inference, baking,
  glTF/blend export, AI parser providers, Blender ops, runtime bindings).

### Next Steps
1. Commit the uncommitted change (`part_graph.py` + `tests/test_connected_components.py`).
2. Fix CI mypy target: `uv run mypy packages/mw_core/src packages/mw_ai/src` (or add `files` to `[tool.mypy]`).
3. Fix the false "no type stubs" comment.
4. Add a test for `min_faces`-reduces-to-one and reconsider the "welded" wording.
5. Implement `geometry/importers.import_mesh` (trimesh.load) to feed `split_connected_components`.
6. Then `geometry/pivots.py` (pivot/axis candidates) — the next ambiguity to solve.

### Handoff Notes
- **`uv` is not installed on this machine.** Run Python tooling directly:
  `python -m pytest`, `python -m mypy packages/mw_core/src packages/mw_ai/src`,
  `python -m ruff check .`. `pyproject` `[tool.pytest.ini_options]` sets
  `pythonpath` so tests import `mw_core`/`mw_ai` without install.
- On Windows, `PYTHONPATH`/`MYPYPATH` use `;` (not `:`). The pyproject
  `mypy_path` uses `:` which is correct for the Linux CI runner only.
- trimesh-dependent tests self-skip if trimesh is absent (`importorskip`).
- Two distinct `Part` classes exist: `mw_core.geometry.part_graph.Part`
  (geometry candidate) vs the `motion_spec` `Part`/`Selector` (schema). They are
  not the same type; a future step maps geometry parts → spec selectors.
- `.claude/` is the user's global skills dir (untracked) — do not commit it.
