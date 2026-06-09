# mw_ai

The AI parser front end. Turns human-written movement intent into a
schema-constrained `motion_spec` proposal using structured outputs / tool use.

The AI has **no execution authority**: it emits JSON only, which `mw_core`
validates and the deterministic compiler interprets. It never writes or runs
Blender Python.
