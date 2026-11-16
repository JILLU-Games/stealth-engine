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

    def test_completed_child_pid_is_not_alive(self):
        # Reproduce a Windows kernel-handle edge case: a PID with a
        # process object still inspectable after the child has exited.
        from stealth_engine.session import _pid_alive

        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(20)"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            self.assertTrue(_pid_alive(child.pid))
        finally:
            child.terminate()
            self.assertIsNotNone(child.wait(timeout=10))
        self.assertFalse(
            _pid_alive(child.pid),
            "terminated child must not block dead-owner profile lock recovery",
        )

    def test_dead_process_lock_is_recovered(self):
        # Child dies without releasing the lock; the OS guard must permit
        # the next process to verify dead PID and safely reclaim ownership.
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            child = """
import os, sys
from stealth_engine import ProfileConfig
from stealth_engine.session import SessionManager
base = sys.argv[1]
mgr = SessionManager(ProfileConfig(profile_name="cross_process", user_data_dir=base), base_dir=base)
mgr.acquire_lock()
os._exit(0)
"""
            completed = subprocess.run(
                [sys.executable, "-c", child, str(base)],
                capture_output=True, text=True, timeout=20, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            cfg = ProfileConfig(profile_name="cross_process", user_data_dir=str(base))
            parent = SessionManager(cfg, base_dir=str(base))
            parent.acquire_lock()
            try:
                self.assertTrue((base / "cross_process" / ".lock").exists())
            finally:
                parent.release_lock()


if __name__ == "__main__":
    unittest.main()
