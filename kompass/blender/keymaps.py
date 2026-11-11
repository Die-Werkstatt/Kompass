# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""One keymap item per pie that has a shortcut."""

import bpy

from ..core.model import MODIFIERS, NATIVE_SLOTS
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
        if len(stored.slots) > NATIVE_SLOTS:
            unknown = (
                f"Blender's pie menu holds {NATIVE_SLOTS} slots, "
                f"it has {len(stored.slots)}"
            )
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


def store(pies):
    """Save the pies and bind their shortcuts."""
    storage.save(pies)
    unregister()
    register()


def _unknown(shortcut):
    if shortcut.key not in _KEYS:
        return f'Blender has no key "{shortcut.key}"'
    if shortcut.space_type not in _SPACE_TYPES:
        return f'Blender has no editor type "{shortcut.space_type}"'
    return None


def text(shortcut):
    """Return the shortcut as Blender names it, such as "Shift Alt Q"."""
    keys = bpy.types.KeyMapItem.bl_rna.properties["type"].enum_items
    key = keys[shortcut.key].name if shortcut.key in keys else shortcut.key
    held = [name.title() for name in MODIFIERS if name in shortcut.modifiers]
    return " ".join([*held, key])


def taken_by(shortcut):
    """Return the name of what Blender runs on the shortcut in its keymap.

    None when the keymap has nothing else on it. Keymaps that are active at
    the same time, such as "Object Mode" beside "3D View", are not searched.
    """
    keymap = bpy.context.window_manager.keyconfigs.user.keymaps.get(shortcut.keymap)
    if keymap is None:
        return None
    for item in keymap.keymap_items:
        if (
            item.active
            and item.type == shortcut.key
            and item.idname != pie.KOMPASS_OT_pie_open.bl_idname
            # -1 is a modifier that may be held or not.
            and all(
                getattr(item, name) in {-1, name in shortcut.modifiers}
                for name in MODIFIERS
            )
        ):
            return item.name
    return None


def unregister():
    for keymap, item in _items:
        keymap.keymap_items.remove(item)
    _items.clear()
