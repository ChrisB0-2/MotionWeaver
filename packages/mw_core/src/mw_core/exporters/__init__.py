"""Exporters: GLB/glTF (baked TRS), .blend, and the canonical sidecar manifest.

The sidecar manifest is the canonical carrier of compiler semantics (limits,
control labels, ids). glTF ``extras`` may mirror *stable ids only*; it is never
the source of truth.
"""

from __future__ import annotations

from mw_core.exporters.manifest_export import build_manifest

__all__ = ["build_manifest"]
