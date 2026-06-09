/**
 * Types for the MotionWeaver sidecar manifest, mirroring the Python
 * `motion_spec` model. The manifest is the canonical carrier of compiler
 * semantics (limits, control labels, stable ids) read alongside the GLB.
 */

export type JointType = "hinge" | "slider" | "spin" | "yaw_pitch";
export type ControlProperty = "angle_deg" | "distance_m";
export type Interp = "step" | "linear" | "cubic";

export interface Keyframe {
  t: number;
  value: number;
  interp?: Interp;
}

export interface Channel {
  control_id: string;
  keyframes: Keyframe[];
}

export interface Clip {
  id: string;
  name: string;
  duration_s?: number;
  loop?: boolean;
  channels: Channel[];
}

export interface Control {
  id: string;
  label: string;
  joint_id: string;
  property: ControlProperty;
  default?: number;
  ui_min?: number;
  ui_max?: number;
}

export interface MotionSpec {
  schema_version: string;
  asset_id: string;
  parts: unknown[];
  joints: unknown[];
  controls: Control[];
  clips: Clip[];
}

export interface Manifest {
  kind: "motionweaver.manifest";
  manifest_version: string;
  motion_spec: MotionSpec;
}

export async function loadManifest(url: string): Promise<Manifest> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`failed to load manifest: ${res.status} ${res.statusText}`);
  }
  const data = (await res.json()) as Manifest;
  if (data.kind !== "motionweaver.manifest") {
    throw new Error(`not a MotionWeaver manifest: kind=${String((data as { kind?: unknown }).kind)}`);
  }
  return data;
}
