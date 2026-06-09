/**
 * MotionWeaver web runtime adapter (reference runtime).
 *
 * Loads a GLB plus its sidecar manifest and returns the scene together with a
 * MotionControls binding. This is the canonical runtime; other engine adapters
 * should match its behavior.
 */

import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Group } from "three";
import { bindControls, type MotionControls } from "./controls";
import { loadManifest, type Manifest } from "./manifest";

export type { Manifest, MotionControls };

export interface LoadedAsset {
  scene: Group;
  manifest: Manifest;
  controls: MotionControls;
}

/**
 * Load a MotionWeaver asset (GLB + sidecar manifest).
 *
 * TODO: wire up an AnimationMixer for baked clips and progress/error reporting.
 */
export async function loadMotionWeaverAsset(glbUrl: string, manifestUrl: string): Promise<LoadedAsset> {
  const loader = new GLTFLoader();
  const [gltf, manifest] = await Promise.all([loader.loadAsync(glbUrl), loadManifest(manifestUrl)]);
  const controls = bindControls(gltf.scene, manifest);
  return { scene: gltf.scene, manifest, controls };
}
