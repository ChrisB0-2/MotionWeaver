# mw_runtime_unity

Placeholder for the Unity runtime adapter (second target after the Three.js
reference runtime). Planned implementation uses **glTFast** to load the GLB and
reads the sidecar manifest (and glTF `extras` stable ids) to bind controls and
clips, optionally via Unity Animation Rigging.

This is intentionally a stub. Keep the adapter thin and the sidecar manifest
canonical so engine adapters do not drift apart.
