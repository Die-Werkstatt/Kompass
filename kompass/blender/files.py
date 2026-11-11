# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Export pies to a file and import them from one."""

from pathlib import Path

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from ..core import model, store, transfer
from . import keymaps, storage


class KOMPASS_OT_pies_export(bpy.types.Operator, ExportHelper):
    """Save pies to a file that Kompass can import"""

    bl_idname = "kompass.pies_export"
    bl_label = "Export Pies"

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})
    # The one pie to export, with the pies it opens. Empty exports all pies.
    pie: bpy.props.StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, _context):
        return bool(storage.pies)

    def invoke(self, context, event):
        # ExportHelper would name the file after the .blend file.
        self.filepath = "kompass-pies.json"
        return super().invoke(context, event)

    def execute(self, _context):
        pies = storage.pies
        if self.pie:
            pies = transfer.with_sub_pies(pies, self.pie)
        try:
            store.save(Path(self.filepath), pies)
        except OSError as error:
            self.report({"ERROR"}, f"Nothing was exported: {error}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Exported {_count(pies)}")
        return {"FINISHED"}


class KOMPASS_OT_pies_import(bpy.types.Operator, ImportHelper):
    """Add the pies of an exported file to your own"""

    bl_idname = "kompass.pies_import"
    bl_label = "Import Pies"

    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})
    # Not remembered: the next import must not replace pies unasked.
    replace: bpy.props.BoolProperty(
        name="Replace My Pies",
        description=(
            "Replace each pie of mine that has the id of a pie in the file. "
            "When off, both are kept"
        ),
        options={"SKIP_SAVE"},
    )

    def execute(self, _context):
        try:
            text = Path(self.filepath).read_text(encoding="utf-8")
            incoming = model.loads(text)
            pies, unbound = transfer.merge(storage.pies, incoming, self.replace)
            storage.save(pies)
        # InvalidPieFile and a file that is not UTF-8 are both ValueError.
        except (OSError, ValueError) as error:
            self.report({"ERROR"}, f"Nothing was imported: {error}")
            return {"CANCELLED"}
        keymaps.unregister()
        keymaps.register()
        if unbound:
            names = ", ".join(f'"{pie.name}"' for pie in unbound)
            self.report(
                {"WARNING"},
                f"Imported {_count(incoming)}. Another pie has the shortcut of {names}",
            )
        else:
            self.report({"INFO"}, f"Imported {_count(incoming)}")
        return {"FINISHED"}


def _count(pies):
    return "1 pie" if len(pies) == 1 else f"{len(pies)} pies"
