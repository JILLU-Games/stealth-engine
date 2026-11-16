"""OS-level private-file acceptance for sensitive config backups and profiles.

This is a runner-local ACL probe. It does not establish security on every
end-user's independently configured filesystem.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import unittest

from stealth_engine import ProfileConfig
from stealth_engine.session import SessionManager


def _windows_private(path: Path) -> None:
    process = subprocess.run(["icacls", str(path)], capture_output=True, text=True, timeout=15)
    if process.returncode != 0:
        raise AssertionError("icacls could not inspect Windows NTFS ACL")
    # A private secret file must not grant read/write to broad principals.
    forbidden = (
        "everyone:", "builtin\\users:", "nt authority\\authenticated users:",
        "s-1-1-0:", "s-1-5-11:", "s-1-5-32-545:",
    )
    lines = [line.strip().lower() for line in process.stdout.splitlines()]
    broad = [line for line in lines if any(k in line for k in forbidden)]
    if broad:
        raise AssertionError("sensitive path has a broad-principal NTFS ACE")


class PrivatePathAcceptance(unittest.TestCase):
    def test_export_and_profile_permissions(self):
        with tempfile.TemporaryDirectory(prefix="stealth-private-") as base:
            root = Path(base)
            cfg = ProfileConfig(
                profile_name="privateprofile",
                user_data_dir=str(root / "privateprofile"),
            )
            profile = SessionManager(cfg, base_dir=str(root))
            profile.ensure_dirs()
            output = root / "privateprofile" / "private-config.json"
            cfg.save_json(output, include_secrets=True)
            self.assertTrue(output.is_file())
            if os.name == "nt":
                _windows_private(output)
                _windows_private(Path(profile.profile_dir))
            else:
                self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE(Path(profile.profile_dir).stat().st_mode), 0o700)


if __name__ == "__main__":
    unittest.main()
