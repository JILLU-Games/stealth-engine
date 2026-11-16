"""Cross-platform real-process profile ownership acceptance tests.

Run on Windows and Linux without browser/network credentials.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from stealth_engine import ProfileConfig
from stealth_engine.exceptions import SessionError
from stealth_engine.session import SessionManager


_CHILD = """
import sys
from stealth_engine import ProfileConfig
from stealth_engine.session import SessionManager
from stealth_engine.exceptions import SessionError
base, action = sys.argv[1:]
cfg = ProfileConfig(profile_name="cross_process", user_data_dir=base)
mgr = SessionManager(cfg, base_dir=base)
try:
    if action == "reset":
        mgr.force_reset()
    else:
        mgr.acquire_lock()
        mgr.release_lock()
    print("ALLOWED")
except SessionError:
    print("DENIED")
"""


class RealSubprocessLockTests(unittest.TestCase):
    def _child(self, base: Path, action: str) -> str:
        result = subprocess.run(
            [sys.executable, "-c", _CHILD, str(base), action],
            capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_os_process_lock_and_reset_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            cfg = ProfileConfig(profile_name="cross_process", user_data_dir=str(base))
            parent = SessionManager(cfg, base_dir=str(base))
            parent.acquire_lock()
            try:
                self.assertEqual(self._child(base, "acquire"), "DENIED")
                self.assertEqual(self._child(base, "reset"), "DENIED")
                self.assertTrue((base / "cross_process" / ".lock").exists())
            finally:
                parent.release_lock()
            self.assertEqual(self._child(base, "acquire"), "ALLOWED")
            self.assertEqual(self._child(base, "reset"), "ALLOWED")
            self.assertFalse((base / "cross_process").exists())


if __name__ == "__main__":
    unittest.main()
