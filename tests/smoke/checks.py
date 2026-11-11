"""Runs inside Blender, started by run.py with Kompass installed and enabled."""

import importlib
import shutil
from pathlib import Path

import addon_utils
import bpy

EXAMPLE = Path(__file__).parent.parent / "data" / "example.json"

# Iterating the collection itself yields add-on entries, not their names.
names = bpy.context.preferences.addons.keys()
(addon,) = [name for name in names if "kompass" in name]
storage = importlib.import_module(addon + ".blender.storage")
preferences = importlib.import_module(addon + ".blender.preferences")


def reenable():
    addon_utils.disable(addon)
    assert not preferences.KompassPreferences.is_registered
    addon_utils.enable(addon)
    assert preferences.KompassPreferences.is_registered


assert preferences.KompassPreferences.is_registered
# A new profile has no pie file.
assert (storage.pies, storage.problem) == ((), None)
path = storage.path()

shutil.copy(EXAMPLE, path)
reenable()
assert [pie.name for pie in storage.pies] == ["Select", "Mesh"]
assert storage.problem is None

path.write_text("{", encoding="utf-8")
reenable()
assert storage.pies == ()
assert not path.exists()
(kept,) = path.parent.glob("pies.invalid-*.json")
assert kept.name in storage.problem

addon_utils.disable(addon)
assert not preferences.KompassPreferences.is_registered
print("Kompass smoke test passed")
