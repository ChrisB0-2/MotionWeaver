// MotionWeaver Unity runtime adapter (placeholder).
//
// Planned: load a GLB via glTFast and parse the sidecar manifest, then hand off
// to MotionWeaverController for control/clip binding. Keep this adapter thin;
// the sidecar manifest remains the canonical source of motion semantics.

using System;
using System.Threading.Tasks;

namespace MotionWeaver
{
    public static class MotionWeaverLoader
    {
        // TODO: implement async load of GLB (glTFast) + sidecar manifest JSON.
        public static Task LoadAsync(string glbPath, string manifestPath)
        {
            throw new NotImplementedException("MotionWeaver Unity loader not implemented yet");
        }
    }
}
