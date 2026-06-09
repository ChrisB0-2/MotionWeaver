// MotionWeaver Unity controller (placeholder).
//
// Planned: expose manifest controls (by stable id) and baked clips on a loaded
// glTF GameObject, mirroring the Three.js MotionControls behavior.

using System;

namespace MotionWeaver
{
    public class MotionWeaverController
    {
        // TODO: resolve manifest control -> joint -> Transform via stable ids
        // mirrored into glTF extras; clamp to ui_min/ui_max; play baked clips.
        public void SetControl(string controlId, float value)
        {
            throw new NotImplementedException("MotionWeaver Unity controller not implemented yet");
        }
    }
}
