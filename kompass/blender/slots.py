# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""What the editor does with the selected slot."""

import bpy

from ..core import edit, model
from . import editor, paint, pie, storage, tools


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
        return edit.place(pies, pie.id, editor.selected(), None)


_SPACES = bpy.types.Space.bl_rna.properties["type"].enum_items

# What the search offers. Blender does not keep the strings of a list that a
# function gives it.
_found = []


def _find():
    """Fill _found with every tool, operator and other pie."""
    _found.clear()
    for space_type, tool, name in tools.every():
        where = _SPACES[space_type].name
        _found.append((f"tool {space_type} {tool}", f"{name} (Tool, {where})", ""))
    for module in dir(bpy.ops):
        for name in dir(getattr(bpy.ops, module)):
            idname = f"{module}.{name}"
            label = pie.operator_type(idname).name
            _found.append((f"operator {idname}", f"{label} ({idname})", ""))
    for stored in storage.pies:
        if stored is not editor.shown():
            _found.append((f"pie {stored.id}", f"{stored.name} (Pie)", ""))


def _content(found):
    """Return the slot content that an entry of _found stands for."""
    kind, _, rest = found.partition(" ")
    if kind == "tool":
        space_type, _, tool = rest.partition(" ")
        return model.ToolSlot(space_type, tool)
    if kind == "operator":
        return model.OperatorSlot(rest)
    return model.SubPieSlot(rest)


class KOMPASS_OT_slot_fill(bpy.types.Operator):
    """Search a tool, an operator or a pie and carry it to a slot"""

    bl_idname = "kompass.slot_fill"
    bl_label = "Add to Pie"
    bl_options = {"INTERNAL"}  # noqa: RUF012
    bl_property = "found"

    found: bpy.props.EnumProperty(items=lambda _self, _context: _found)

    @classmethod
    def poll(cls, _context):
        return editor.shown() is not None and not editor.preview

    def invoke(self, context, _event):
        _find()
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}

    def execute(self, context):
        carrying = editor.carried is not None
        editor.carried = _content(self.found)
        editor.redraw(context)
        if not carrying:
            bpy.ops.kompass.slot_carry("INVOKE_DEFAULT")
        return {"FINISHED"}


class KOMPASS_OT_slot_carry(bpy.types.Operator):
    """Runs while something is carried, to let Esc and a right-click drop it"""

    bl_idname = "kompass.slot_carry"
    bl_label = "Carry to Slot"
    bl_options = {"INTERNAL"}  # noqa: RUF012

    def invoke(self, context, _event):
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if editor.carried is None:
            return {"FINISHED"}
        if event.type in {"ESC", "RIGHTMOUSE"} and event.value == "PRESS":
            editor.carried = None
            editor.redraw(context)
            return {"CANCELLED"}
        # The canvas follows the pointer and takes the click that places.
        return {"PASS_THROUGH"}


class KOMPASS_OT_slot_place(editor.Edit, bpy.types.Operator):
    """Put what is carried into the slot and carry what the slot held"""

    bl_idname = "kompass.slot_place"
    bl_label = "Place in Slot"

    slot: bpy.props.IntProperty()

    @classmethod
    def poll(cls, _context):
        return editor.carried is not None

    def edited(self, pies, pie):
        return edit.place(pies, pie.id, self.slot, editor.carried)

    def execute(self, context):
        held = editor.shown().slots[self.slot]
        result = super().execute(context)
        if result == {"FINISHED"}:
            editor.carried = held
            editor.select(self.slot)
        return result


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
        self.layout.operator(KOMPASS_OT_slot_fill.bl_idname, icon="ADD")
        slot = editor.selected()
        if slot is None:
            self.layout.label(text="No slot selected")
            return
        self.layout.label(text=_names(editor.shown())[slot])
        row = self.layout.row(align=True)
        row.operator(KOMPASS_OT_slot_clear.bl_idname, text="Clear", icon="X")
        row.menu(KOMPASS_MT_slot_swap.bl_idname)
