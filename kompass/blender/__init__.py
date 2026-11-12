# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Everything that needs Blender."""

import bpy

# The add-on's identifier is the package above this one.
ADDON = __package__.rpartition(".")[0]

# These read ADDON while they load.
from . import (
    canvas,
    editor,
    files,
    keymaps,
    live,
    pie,
    preferences,
    shortcuts,
    slots,
    storage,
)

_CLASSES = (
    preferences.KompassPreferences,
    pie.KOMPASS_OT_pie_open,
    live.KOMPASS_OT_pie_live,
    files.KOMPASS_OT_pies_export,
    files.KOMPASS_OT_pies_import,
    editor.KompassTree,
    editor.KOMPASS_OT_editor_open,
    editor.KOMPASS_OT_editor_show,
    editor.KOMPASS_OT_editor_preview,
    editor.KOMPASS_OT_pie_add,
    editor.KOMPASS_OT_pie_rename,
    editor.KOMPASS_OT_pie_duplicate,
    editor.KOMPASS_OT_pie_delete,
    editor.KOMPASS_OT_pie_slots,
    editor.KOMPASS_PT_viewport,
    editor.KOMPASS_PT_pies,
    shortcuts.KOMPASS_OT_pie_shortcut,
    shortcuts.KOMPASS_OT_pie_unbind,
    shortcuts.KOMPASS_OT_pie_context,
    shortcuts.KOMPASS_PT_shortcut,
    slots.KOMPASS_OT_slot_fill,
    slots.KOMPASS_OT_slot_group,
    slots.KOMPASS_OT_slot_open,
    slots.KOMPASS_OT_slot_clear,
    slots.KOMPASS_OT_slot_label,
    slots.KOMPASS_OT_slot_icon,
    slots.KOMPASS_OT_slot_settings,
    slots.KOMPASS_OT_slot_swap,
    slots.KOMPASS_MT_slot_swap,
    slots.KOMPASS_MT_slot,
    canvas.KOMPASS_GT_slot,
    canvas.KOMPASS_GT_dial,
    canvas.KOMPASS_GGT_canvas,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    storage.load()
    keymaps.register()
    canvas.register()


def unregister():
    live.close()
    canvas.unregister()
    keymaps.unregister()
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
