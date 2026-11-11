"""Build the extension, install it into an empty Blender profile and run a
check script inside Blender. Exits 127 when Blender is not installed, which
the suite reports as skipped.

    python3 tests/smoke/run.py                          # checks.py, no window
    xvfb-run -a python3 tests/smoke/run.py --interface  # interface.py, needs a display
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent


def main():
    blender = shutil.which("blender")
    if blender is None:
        print("blender is not on PATH")
        return 127
    if "--interface" in sys.argv:
        check = ["--enable-event-simulate", "--python", str(HERE / "interface.py")]
    else:
        check = ["--background", "--python-exit-code", "1"]
        check += ["--python", str(HERE / "checks.py")]
    with tempfile.TemporaryDirectory() as profile:
        package = Path(profile) / "kompass.zip"
        # Blender reads and writes all user files here, not in the real profile.
        env = {**os.environ, "BLENDER_USER_RESOURCES": profile}
        steps = [
            ["--command", "extension", "build"]
            + ["--source-dir", str(ROOT / "kompass")]
            + ["--output-filepath", str(package)],
            ["--command", "extension", "install-file"]
            + ["--repo", "user_default", "--enable", str(package)],
            check,
        ]
        for step in steps:
            result = subprocess.run([blender, *step], env=env, check=False)
            if result.returncode != 0:
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
