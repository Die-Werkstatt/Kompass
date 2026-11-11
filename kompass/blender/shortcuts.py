# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""The editor's panel for the shortcut of the pie on the canvas."""

import bpy

from ..core import edit, model
from . import editor, keymaps

# Whether the next key press becomes the shortcut.
_listening = False

_HELD = frozenset(
    {
        "LEFT_CTRL",
        "RIGHT_CTRL",
        "LEFT_SHIFT",
        "RIGHT_SHIFT",
        "LEFT_ALT",
        "RIGHT_ALT",
        "OSKEY",
        "HYPER",
    }
)


class KOMPASS_OT_pie_shortcut(editor.Edit, bpy.types.Operator):
    """Press the keys that open this pie. Esc or a click keeps the old ones"""

    bl_idname = "kompass.pie_shortcut"
    bl_label = "Set Shortcut"

    def invoke(self, context, _event):
        global _listening
        _listening = True
        context.window_manager.modal_handler_add(self)
        editor.redraw(context)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        global _listening
        if event.value != "PRESS" or event.type in _HELD:
            return {"RUNNING_MODAL"}
        _listening = False
        if event.type == "ESC" or "MOUSE" in event.type:
            editor.redraw(context)
            return {"CANCELLED"}
        self.pressed = (
            event.type,
            frozenset(name for name in model.MODIFIERS if getattr(event, name, False)),
        )
        return self.execute(context)

    def edited(self, pies, pie):
        key, modifiers = self.pressed
        keymap, space_type = keymaps.CONTEXTS[0][:2]
        if pie.shortcut is not None:
            keymap, space_type = pie.shortcut.keymap, pie.shortcut.space_type
        shortcut = model.Shortcut(keymap, space_type, key, modifiers)
        return edit.bind(pies, pie.id, shortcut)


class KOMPASS_OT_pie_unbind(editor.Edit, bpy.types.Operator):
    """Take the shortcut off this pie"""

    bl_idname = "kompass.pie_unbind"
    bl_label = "Remove Shortcut"

    @classmethod
    def poll(cls, _context):
        pie = editor.shown()
        return pie is not None and pie.shortcut is not None

    def edited(self, pies, pie):
        return edit.bind(pies, pie.id, None)


class KOMPASS_OT_pie_context(editor.Edit, bpy.types.Operator):
    """Choose where the shortcut opens this pie"""

    bl_idname = "kompass.pie_context"
    bl_label = "Shortcut Context"

    keymap: bpy.props.EnumProperty(
        items=[(keymap, name, "") for keymap, _, name in keymaps.CONTEXTS]
    )

    @classmethod
    def poll(cls, context):
        return KOMPASS_OT_pie_unbind.poll(context)

    def edited(self, pies, pie):
        space_type = next(
            space_type
            for keymap, space_type, _ in keymaps.CONTEXTS
            if keymap == self.keymap
        )
        shortcut = model.Shortcut(
            self.keymap, space_type, pie.shortcut.key, pie.shortcut.modifiers
        )
        return edit.bind(pies, pie.id, shortcut)


class KOMPASS_PT_shortcut(bpy.types.Panel):
    bl_label = "Shortcut"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Kompass"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.tree_type == editor.KompassTree.bl_idname and editor.shown()

    def draw(self, _context):
        pie = editor.shown()
        shortcut = pie.shortcut
        text = "Set Shortcut" if shortcut is None else keymaps.text(shortcut)
        row = self.layout.row(align=True)
        row.operator(
            KOMPASS_OT_pie_shortcut.bl_idname,
            text="Press a Key" if _listening else text,
            depress=_listening,
        )
        row.operator(KOMPASS_OT_pie_unbind.bl_idname, text="", icon="X")
        if shortcut is None:
            return
        names = {keymap: name for keymap, _, name in keymaps.CONTEXTS}
        self.layout.operator_menu_enum(
            KOMPASS_OT_pie_context.bl_idname,
            "keymap",
            text=names.get(shortcut.keymap, shortcut.keymap),
        )
        for warning in keymaps.warnings(pie):
            self.layout.label(text=warning, icon="ERROR")
