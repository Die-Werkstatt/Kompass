# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Everything that needs Blender."""

import importlib.util

import bpy

# The add-on's identifier is the package above this one.
ADDON = __package__.rpartition(".")[0]
# Kompass Native ships without live.py, which draws the Kompass pie.
DRAWABLE = importlib.util.find_spec(".live", __package__) is not None
# The id of each edition in its manifest, and its name.
EDITIONS = {"kompass": "Kompass", "kompass_native": "Kompass Native"}

# These read ADDON while they load.
from . import (
    canvas,
    editor,
    files,
    keymaps,
    pie,
    preferences,
    shortcuts,
    slots,
    storage,
)

_CLASSES = (
    preferences.KompassPreferences,
    pie.KOMPASS_OT_pie_open,
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
if DRAWABLE:
    from . import live

    _CLASSES += (live.KOMPASS_OT_pie_live,)


def register():
    _refuse_second_edition()
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    storage.load()
    keymaps.register()
    canvas.register()


def _refuse_second_edition():
    # Both editions register the same operators. Blender reports the error
    # and leaves this one off.
    if not hasattr(bpy.types, pie.KOMPASS_OT_pie_open.__name__):
        return
    other = next(
        (
            EDITIONS[name.rpartition(".")[2]]
            for name in (entry.module for entry in bpy.context.preferences.addons)
            if name != ADDON and name.rpartition(".")[2] in EDITIONS
        ),
        "Kompass",
    )
    raise RuntimeError(f"Turn off {other} first: only one Kompass can be on")


def unregister():
    if DRAWABLE:
        live.close()
        live.drop()
    canvas.unregister()
    keymaps.unregister()
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
