# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender

import bpy

from . import ADDON, editor, files, keymaps, storage


class KompassPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON

    def draw(self, _context):
        layout = self.layout
        row = layout.row()
        row.label(text=f"Pies: {len(storage.pies)}")
        row.operator(editor.KOMPASS_OT_editor_open.bl_idname)
        row.operator(files.KOMPASS_OT_pies_import.bl_idname, text="Import")
        row.operator(files.KOMPASS_OT_pies_export.bl_idname, text="Export All")
        for stored in storage.pies:
            self._draw_pie(layout.box(), stored)
        layout.label(text=str(storage.path()), icon="FILE")
        for problem in filter(None, [storage.problem, *keymaps.problems]):
            layout.label(text=problem, icon="ERROR")

    def _draw_pie(self, box, stored):
        row = box.row()
        row.label(text=stored.name)
        shortcut = stored.shortcut
        if shortcut is not None:
            row.label(text=f"{keymaps.text(shortcut)} in {shortcut.keymap}")
        export = row.operator(
            files.KOMPASS_OT_pies_export.bl_idname, text="", icon="EXPORT"
        )
        export.pie = stored.id
        taken = shortcut and keymaps.taken_by(shortcut)
        if taken:
            box.label(text=f'Blender also has "{taken}" on it', icon="ERROR")
