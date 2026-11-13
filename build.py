# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Builds both editions into this folder. Blender runs it:

    blender --background --factory-startup --python-exit-code 1 --python build.py

kompass-<version>.zip is Kompass. kompass_native-<version>.zip is Kompass
Native: the same add-on without live.py, which draws the Kompass pie.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import bpy
import tomllib

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "kompass"
# The manifest lines of Kompass Native that differ from Kompass's.
NATIVE = {"id": "kompass_native", "name": "Kompass Native"}


def native_manifest(text):
    lines = text.splitlines(keepends=True)
    for key, value in NATIVE.items():
        found = [n for n, line in enumerate(lines) if line.startswith(f"{key} = ")]
        if len(found) != 1:
            raise SystemExit(f'The manifest needs one "{key} = " line')
        lines[found[0]] = f'{key} = "{value}"\n'
    return "".join(lines)


def build(source, edition):
    with (source / "blender_manifest.toml").open("rb") as manifest:
        version = tomllib.load(manifest)["version"]
    output = HERE / f"{edition}-{version}.zip"
    command = [bpy.app.binary_path, "--command", "extension", "build"]
    command += ["--source-dir", str(source), "--output-filepath", str(output)]
    subprocess.run(command, check=True)


def main():
    build(SOURCE, "kompass")
    with tempfile.TemporaryDirectory() as folder:
        native = Path(folder) / "kompass"
        shutil.copytree(SOURCE, native, ignore=shutil.ignore_patterns("__pycache__"))
        (native / "blender" / "live.py").unlink()
        manifest = native / "blender_manifest.toml"
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text(native_manifest(text), encoding="utf-8")
        build(native, "kompass_native")


main()
