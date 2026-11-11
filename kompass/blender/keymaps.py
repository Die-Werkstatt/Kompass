# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""One keymap item per pie that has a shortcut."""

import bpy

from . import pie, storage

_KEYS = frozenset(bpy.types.KeyMapItem.bl_rna.properties["type"].enum_items.keys())
_SPACE_TYPES = frozenset(
    bpy.types.KeyMap.bl_rna.properties["space_type"].enum_items.keys()
)

_items = []
# One line per shortcut that could not be set.
problems = []


def register():
    problems.clear()
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    # Blender has no add-on key configuration in background mode.
    if keyconfig is None:
        return
    for stored in storage.pies:
        shortcut = stored.shortcut
        if shortcut is None:
            continue
        unknown = _unknown(shortcut)
        if unknown:
            problems.append(f'Pie "{stored.name}" has no shortcut: {unknown}')
            continue
        keymap = keyconfig.keymaps.new(
            name=shortcut.keymap, space_type=shortcut.space_type
        )
        item = keymap.keymap_items.new(
            pie.KOMPASS_OT_pie_open.bl_idname,
            shortcut.key,
            "PRESS",
            **{name: True for name in shortcut.modifiers},
        )
        item.properties.pie = stored.id
        _items.append((keymap, item))


def _unknown(shortcut):
    if shortcut.key not in _KEYS:
        return f'Blender has no key "{shortcut.key}"'
    if shortcut.space_type not in _SPACE_TYPES:
        return f'Blender has no editor type "{shortcut.space_type}"'
    return None


def unregister():
    for keymap, item in _items:
        keymap.keymap_items.remove(item)
    _items.clear()
