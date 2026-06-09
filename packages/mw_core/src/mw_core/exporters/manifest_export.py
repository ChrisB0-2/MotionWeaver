"""Build the canonical sidecar manifest from a ``motion_spec``.

The manifest is a plain JSON document a runtime adapter reads alongside the GLB.
For v1 it is the validated spec itself plus a small header recording provenance.
Keeping this real (not a stub) lets the export round-trip test exercise the full
spec -> manifest -> spec path.
"""

from __future__ import annotations

from typing import Any

from mw_core.motion_spec.models import MotionSpec

MANIFEST_KIND = "motionweaver.manifest"
MANIFEST_VERSION = "0.1.0"


def build_manifest(spec: MotionSpec) -> dict[str, Any]:
    """Return a JSON-serializable manifest dict for ``spec``."""
    return {
        "kind": MANIFEST_KIND,
        "manifest_version": MANIFEST_VERSION,
        "motion_spec": spec.model_dump(mode="json", exclude_none=True),
    }


def spec_from_manifest(manifest: dict[str, Any]) -> MotionSpec:
    """Inverse of :func:`build_manifest`: parse a manifest back into a MotionSpec."""
    if manifest.get("kind") != MANIFEST_KIND:
        raise ValueError(f"not a MotionWeaver manifest: kind={manifest.get('kind')!r}")
    return MotionSpec.model_validate(manifest["motion_spec"])
