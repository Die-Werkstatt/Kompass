# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender

import bpy

from . import ADDON, keymaps, storage


class KompassPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON

    def draw(self, _context):
        layout = self.layout
        layout.label(text=f"Pies: {len(storage.pies)}")
        layout.label(text=str(storage.path()), icon="FILE")
        for problem in filter(None, [storage.problem, *keymaps.problems]):
            layout.label(text=problem, icon="ERROR")
