"""Build wheel/sdist and prove fresh, out-of-tree install on the current OS."""
from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


def main() -> None:
    root = Path.cwd()
    subprocess.run([sys.executable, "-m", "build", "--outdir", "dist"], check=True)
    wheels = sorted(root.glob("dist/*.whl"))
    sdists = sorted(root.glob("dist/*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError("Expected exactly one wheel and one source distribution")
    subprocess.run([sys.executable, "-m", "twine", "check", str(wheels[0]), str(sdists[0])], check=True)

    with tempfile.TemporaryDirectory(prefix="stealth-package-") as directory:
        sandbox = Path(directory)
        env_dir = sandbox / "venv"
        venv.EnvBuilder(with_pip=True).create(env_dir)
        python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(python), "-m", "pip", "install", str(wheels[0])], check=True, cwd=sandbox)
        subprocess.run([str(python), "-m", "pip", "check"], check=True, cwd=sandbox)
        # Run from OUTSIDE the repository: a local source-tree import would be a false pass.
        subprocess.run(
            [str(python), "-c", (
                "import importlib.metadata as m; import stealth_engine; "
                "from stealth_engine import ProfileConfig, StealthEngine; "
                "print('Installed package:', m.version('stealth_engine')); "
                "assert m.version('stealth_engine') == '0.3.0'"
            )],
            check=True,
            cwd=sandbox,
        )
    print("PACKAGE GATE PASS: wheel, sdist and fresh install imported successfully")


if __name__ == "__main__":
    main()
