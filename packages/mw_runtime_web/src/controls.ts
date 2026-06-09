/**
 * Maps manifest controls/clips onto a loaded glTF scene so a host app can drive
 * joints by control id or play baked clips.
 */

import type { AnimationClip, Object3D } from "three";
import type { Manifest } from "./manifest";

export interface MotionControls {
  /** Stable control ids declared in the manifest. */
  controlIds(): string[];
  /**
   * Set a control's value (degrees for angular joints, meters for sliders).
   * TODO: drive the corresponding node transform, clamped to ui_min/ui_max.
   */
  setControl(controlId: string, value: number): void;
  /** Baked animation clips parsed from the GLB. */
  clips(): AnimationClip[];
}

/**
 * Bind a manifest to a loaded glTF root.
 *
 * TODO: resolve manifest control -> joint -> glTF node (via stable ids mirrored
 * into glTF `extras`), and expose set/play operations through an AnimationMixer.
 */
export function bindControls(_root: Object3D, _manifest: Manifest): MotionControls {
  throw new Error("bindControls is not implemented yet");
}
