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

# Every operator setting in the example file is one this Blender has.
for pie in storage.pies:
    for slot in pie.slots:
        for name in getattr(slot, "properties", {}):
            module, _, operator = slot.idname.partition(".")
            known = getattr(getattr(bpy.ops, module), operator).get_rna_type()
            assert name in known.properties, (slot.idname, name)

# Export all pies, or one pie with the pies it opens.
exported = path.with_name("exported.json")
assert bpy.ops.kompass.pies_export(filepath=str(exported)) == {"FINISHED"}
assert exported.read_bytes() == EXAMPLE.read_bytes()
assert bpy.ops.kompass.pies_export(filepath=str(exported), pie="mesh") == {"FINISHED"}
assert '"select"' not in exported.read_text(encoding="utf-8")

# Importing keeps both pies with one id unless told to replace.
assert bpy.ops.kompass.pies_import(filepath=str(EXAMPLE)) == {"FINISHED"}
assert [pie.id for pie in storage.pies] == ["select", "mesh", "select-2", "mesh-2"]
assert bpy.ops.kompass.pies_import(filepath=str(EXAMPLE), replace=True) == {"FINISHED"}
assert len(storage.pies) == 4
reenable()
assert len(storage.pies) == 4

# Every slot of the starter pies names an operator of this Blender and
# settings that it has.
files = importlib.import_module(addon + ".blender.files")
model = importlib.import_module(addon + ".core.model")
pie_menu = importlib.import_module(addon + ".blender.pie")
for starter in model.loads(files.STARTER.read_text(encoding="utf-8")):
    for slot in starter.slots:
        if isinstance(slot, model.OperatorSlot):
            known = pie_menu.operator_type(slot.idname)
            assert known is not None, slot.idname
            assert set(slot.properties) <= set(known.properties.keys()), slot

# The editor's pie operators change the pie on the canvas and the file.
editor = importlib.import_module(addon + ".blender.editor")
assert bpy.ops.kompass.pie_add() == {"FINISHED"}
assert editor.shown().id == "pie"
assert bpy.ops.kompass.pie_rename(name=" Edges ") == {"FINISHED"}
assert bpy.ops.kompass.pie_duplicate() == {"FINISHED"}
assert (editor.shown().id, editor.shown().name) == ("pie-2", "Edges Copy")
assert bpy.ops.kompass.pie_delete() == {"FINISHED"}
assert [pie.name for pie in storage.pies][-1] == "Edges"
try:
    bpy.ops.kompass.pie_rename(name=" ")
except RuntimeError as error:
    assert "empty name" in str(error), error
else:
    raise AssertionError("a pie was given an empty name")
bpy.ops.kompass.editor_show(pie="pie")
assert bpy.ops.kompass.pie_delete() == {"FINISHED"}
assert len(storage.pies) == 4
reenable()
assert len(storage.pies) == 4

# A file that is not a pie file changes nothing and says why.
exported.write_text('{"schema_version": 2, "pies": []}', encoding="utf-8")
try:
    bpy.ops.kompass.pies_import(filepath=str(exported))
except RuntimeError as error:
    assert "newer Kompass" in str(error), error
else:
    raise AssertionError("an unreadable file was imported")
assert len(storage.pies) == 4

path.write_text("{", encoding="utf-8")
reenable()
assert storage.pies == ()
assert not path.exists()
(kept,) = path.parent.glob("pies.invalid-*.json")
assert kept.name in storage.problem

addon_utils.disable(addon)
assert not preferences.KompassPreferences.is_registered
print("Kompass smoke test passed")
