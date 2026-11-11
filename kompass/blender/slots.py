# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""What the editor does with the selected slot."""

import bpy

from ..core import edit, model
from . import editor, paint


def _names(pie):
    """Return what a menu calls each slot: where it is and what it holds."""
    return [
        f"{model.slot_name(pie, slot)}: {text.title() or 'Empty'}"
        for slot, (text, _, _) in enumerate(paint.labels(pie))
    ]


class KOMPASS_OT_slot_clear(editor.Edit, bpy.types.Operator):
    """Empty the selected slot"""

    bl_idname = "kompass.slot_clear"
    bl_label = "Clear Slot"

    @classmethod
    def poll(cls, _context):
        slot = editor.selected()
        return slot is not None and editor.shown().slots[slot] is not None

    def edited(self, pies, pie):
        return edit.clear(pies, pie.id, editor.selected())


class KOMPASS_OT_slot_swap(editor.Edit, bpy.types.Operator):
    """Exchange what the selected slot and this slot hold"""

    bl_idname = "kompass.slot_swap"
    bl_label = "Swap Slots"

    other: bpy.props.IntProperty()

    @classmethod
    def poll(cls, _context):
        return editor.selected() is not None

    def edited(self, pies, pie):
        slot = editor.selected()
        # The selection stays with what was selected.
        editor.select(self.other)
        return edit.swap(pies, pie.id, slot, self.other)


class KOMPASS_MT_slot_swap(bpy.types.Menu):
    bl_idname = "KOMPASS_MT_slot_swap"
    bl_label = "Swap With"

    def draw(self, _context):
        for slot, name in enumerate(_names(editor.shown())):
            if slot != editor.selected():
                button = self.layout.operator(KOMPASS_OT_slot_swap.bl_idname, text=name)
                button.other = slot


class KOMPASS_PT_slot(bpy.types.Panel):
    bl_label = "Slot"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Kompass"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.tree_type == editor.KompassTree.bl_idname and not editor.preview

    def draw(self, _context):
        slot = editor.selected()
        if slot is None:
            self.layout.label(text="No slot selected")
            return
        self.layout.label(text=_names(editor.shown())[slot])
        row = self.layout.row(align=True)
        row.operator(KOMPASS_OT_slot_clear.bl_idname, text="Clear", icon="X")
        row.menu(KOMPASS_MT_slot_swap.bl_idname)
