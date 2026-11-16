"""Live WebGL readback acceptance on actual Camoufox; not a spoof guarantee."""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

from stealth_engine import ProfileConfig, StealthEngine


class WebGLReadbackAcceptance(unittest.IsolatedAsyncioTestCase):
    async def test_live_webgl_consecutive_reads_and_canvas_mutation(self):
        with tempfile.TemporaryDirectory(prefix="webgl-ci-") as base:
            cfg = ProfileConfig(
                profile_name="webgl", user_data_dir=str(Path(base) / "webgl"),
                os="windows" if __import__("os").name == "nt" else "linux",
                # Linux: headed Firefox inside CI Xvfb + Mesa software GL;
                # Windows: real headless Firefox using the host's GL stack.
                headless=(__import__("os").name == "nt"),
                geoip=False, seed=5823, js_noise=True,
            )
            session = await StealthEngine(cfg).alaunch()
            try:
                page = session.page
                await page.goto("about:blank")
                data = await page.evaluate("""() => {
                    const canvas = document.createElement('canvas');
                    canvas.width = 8; canvas.height = 8;
                    const gl = canvas.getContext('webgl', {preserveDrawingBuffer:true});
                    if (!gl) return {supported: false};
                    gl.viewport(0,0,8,8);
                    const read = () => {
                      const bytes = new Uint8Array(4);
                      gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,bytes);
                      return Array.from(bytes);
                    };
                    gl.clearColor(.2,.4,.6,1);
                    gl.clear(gl.COLOR_BUFFER_BIT);
                    const first = read();
                    const second = read();
                    gl.clearColor(.8,.1,.2,1);
                    gl.clear(gl.COLOR_BUFFER_BIT);
                    const changed = read();
                    return {
                      supported: true, first, second, changed,
                      error: gl.getError()
                    };
                }""")
                self.assertTrue(data["supported"], "real WebGL context unavailable on runner")
                self.assertEqual(data["first"], data["second"])
                self.assertNotEqual(data["first"], data["changed"])
                self.assertEqual(data["error"], 0)
            finally:
                await session.aclose()
