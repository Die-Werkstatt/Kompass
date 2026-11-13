"""Build both editions, install them into an empty Blender profile with one
turned on, and run a check script inside Blender. Exits 127 when Blender is
not installed, which the suite reports as skipped.

    python3 tests/smoke/run.py                          # checks.py, each edition
    xvfb-run -a python3 tests/smoke/run.py --interface  # interface.py, Kompass
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import tomllib

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
EDITIONS = ("kompass", "kompass_native")


def main():
    blender = shutil.which("blender")
    if blender is None:
        print("blender is not on PATH")
        return 127
    if "--interface" in sys.argv:
        check = ["--enable-event-simulate", "--python", str(HERE / "interface.py")]
        editions = EDITIONS[:1]
    else:
        check = ["--background", "--python-exit-code", "1"]
        check += ["--python", str(HERE / "checks.py")]
        editions = EDITIONS
    build = ["--background", "--factory-startup", "--python-exit-code", "1"]
    built = subprocess.run(
        [blender, *build, "--python", str(ROOT / "build.py")], check=False
    )
    if built.returncode != 0:
        return 1
    with (ROOT / "kompass" / "blender_manifest.toml").open("rb") as manifest:
        version = tomllib.load(manifest)["version"]
    for edition in editions:
        (other,) = set(EDITIONS) - {edition}
        with tempfile.TemporaryDirectory() as profile:
            # Blender reads and writes all user files here, not in the real profile.
            env = {**os.environ, "BLENDER_USER_RESOURCES": profile}
            install = [
                "--command",
                "extension",
                "install-file",
                "--repo",
                "user_default",
            ]
            steps = [
                [*install, str(ROOT / f"{other}-{version}.zip")],
                [*install, "--enable", str(ROOT / f"{edition}-{version}.zip")],
                check,
            ]
            for step in steps:
                result = subprocess.run([blender, *step], env=env, check=False)
                if result.returncode != 0:
                    return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
