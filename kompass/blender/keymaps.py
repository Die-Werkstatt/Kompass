# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""One keymap item per pie that has a shortcut."""

import bpy

from ..core.model import MODIFIERS
from . import pie, storage

_KEYS = frozenset(bpy.types.KeyMapItem.bl_rna.properties["type"].enum_items.keys())
_SPACE_TYPES = frozenset(
    bpy.types.KeyMap.bl_rna.properties["space_type"].enum_items.keys()
)

# Where a shortcut can open a pie: a keymap of Blender's, the space type
# KeyMaps.new() needs for it, and what the editor calls it.
CONTEXTS = (
    ("3D View", "VIEW_3D", "3D Viewport"),
    ("Object Mode", "EMPTY", "Object Mode"),
    ("Mesh", "EMPTY", "Mesh Edit Mode"),
    ("Curve", "EMPTY", "Curve Edit Mode"),
    ("Armature", "EMPTY", "Armature Edit Mode"),
    ("Pose", "EMPTY", "Pose Mode"),
    ("Sculpt", "EMPTY", "Sculpt Mode"),
    ("Vertex Paint", "EMPTY", "Vertex Paint"),
    ("Weight Paint", "EMPTY", "Weight Paint"),
    ("Image Paint", "EMPTY", "Texture Paint"),
    ("UV Editor", "EMPTY", "UV Editor"),
    ("Image", "IMAGE_EDITOR", "Image Editor"),
    ("Node Editor", "NODE_EDITOR", "Node Editor"),
    ("Sequencer", "SEQUENCE_EDITOR", "Video Sequencer"),
    ("Window", "EMPTY", "Everywhere"),
)


# The keymap of an editor, and the keymaps of its modes. In a mode Blender
# looks for a key in the mode's keymap, then in the editor's, then in
# "Window". Run in Blender 5.2.4; the manual does not give the order.
_MODES = {
    "3D View": (
        "Object Mode",
        "Mesh",
        "Curve",
        "Armature",
        "Pose",
        "Sculpt",
        "Vertex Paint",
        "Weight Paint",
        "Image Paint",
    ),
    "Image": ("UV Editor",),
}
# Keymaps of Blender's that are searched with one of ours.
_WITH = {"3D View": ("3D View Generic",), "Object Mode": ("Object Non-modal",)}


def _before(keymap):
    """Return the keymaps Blender looks in before that one."""
    if keymap == "Window":
        return [name for name, _, _ in CONTEXTS if name != "Window"]
    return list(_MODES.get(keymap, ()))


def context(shortcut):
    """Return what the editor calls the place where the shortcut opens its pie."""
    names = {keymap: name for keymap, _, name in CONTEXTS}
    return names.get(shortcut.keymap, shortcut.keymap)


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
        if not pie.opens(stored):
            problems.append(f'Pie "{stored.name}" has no shortcut: {pie.TOO_WIDE}')
            continue
        keymap = keyconfig.keymaps.new(
            name=shortcut.keymap, space_type=shortcut.space_type
        )
        item = keymap.keymap_items.new(
            pie.LIVE if pie.drawn(stored) else pie.KOMPASS_OT_pie_open.bl_idname,
            shortcut.key,
            "PRESS",
            **{name: True for name in shortcut.modifiers},
        )
        item.properties.pie = stored.id
        _items.append((keymap, item))


def store(pies):
    """Save the pies and bind their shortcuts."""
    storage.save(pies)
    rebind()


def rebind():
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


def taken_by(shortcut, keymap=None):
    """Return the name of what Blender runs on the shortcut's keys in that
    keymap, the shortcut's own unless one is given, or None."""
    keymap = keymap or shortcut.keymap
    keymaps = bpy.context.window_manager.keyconfigs.user.keymaps
    for name in (keymap, *_WITH.get(keymap, ())):
        for item in getattr(keymaps.get(name), "keymap_items", ()):
            if (
                item.active
                and item.type == shortcut.key
                and item.idname not in {pie.KOMPASS_OT_pie_open.bl_idname, pie.LIVE}
                # -1 is a modifier that may be held or not.
                and all(
                    getattr(item, held) in {-1, held in shortcut.modifiers}
                    for held in MODIFIERS
                )
            ):
                return item.name
    return None


def warnings(stored):
    """Return what keeps the pie's shortcut from opening it, or from being
    the only thing on its keys."""
    found = [line for line in problems if line.startswith(f'Pie "{stored.name}" ')]
    shortcut = stored.shortcut
    if shortcut is None:
        return found
    taken = taken_by(shortcut)
    if taken:
        found.append(f'Blender also has "{taken}" on it')
    for other in storage.pies:
        if other is not stored and other.shortcut == shortcut:
            found.append(f'Pie "{other.name}" has the same shortcut')
    names = {keymap: name for keymap, _, name in CONTEXTS}
    keys = shortcut.key, shortcut.modifiers
    for keymap in _before(shortcut.keymap):
        taken = taken_by(shortcut, keymap)
        if taken:
            found.append(f'In {names[keymap]} Blender runs "{taken}" instead')
        for other in storage.pies:
            there = other.shortcut
            if (
                there
                and there.keymap == keymap
                and (there.key, there.modifiers) == keys
            ):
                found.append(f'In {names[keymap]} pie "{other.name}" opens instead')
    return found


def unregister():
    for keymap, item in _items:
        keymap.keymap_items.remove(item)
    _items.clear()
