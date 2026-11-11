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


class KOMPASS_OT_slot_fill(editor.Edit, bpy.types.Operator):
    """Search a tool, an operator or a pie and put it in the selected slot"""

    bl_idname = "kompass.slot_fill"
    bl_label = "Fill Slot"
    bl_property = "found"

    found: bpy.props.EnumProperty(items=lambda _self, _context: _found)

    @classmethod
    def poll(cls, _context):
        return editor.selected() is not None

    def invoke(self, context, _event):
        _find()
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}

    def edited(self, pies, pie):
        return edit.place(pies, pie.id, editor.selected(), _content(self.found))


class KOMPASS_OT_slot_group(editor.Edit, bpy.types.Operator):
    """Add a pie and let the selected slot open it as a sub-pie"""

    bl_idname = "kompass.slot_group"
    bl_label = "New Sub-Pie"

    @classmethod
    def poll(cls, _context):
        return editor.selected() is not None

    def edited(self, pies, pie):
        pies = edit.add(pies, "Sub-Pie")
        content = model.SubPieSlot(pies[-1].id)
        return edit.place(pies, pie.id, editor.selected(), content)


class KOMPASS_OT_slot_open(bpy.types.Operator):
    """Show the sub-pie of the selected slot"""

    bl_idname = "kompass.slot_open"
    bl_label = "Open Sub-Pie"
    bl_options = {"INTERNAL"}  # noqa: RUF012

    @classmethod
    def poll(cls, _context):
        slot = editor.selected()
        if slot is None:
            return False
        return isinstance(editor.shown().slots[slot], model.SubPieSlot)

    def execute(self, context):
        editor.enter(editor.selected())
        editor.redraw(context)
        return {"FINISHED"}


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


class KOMPASS_MT_slot(bpy.types.Menu):
    bl_idname = "KOMPASS_MT_slot"
    bl_label = "Slot"

    def draw(self, _context):
        filled = editor.shown().slots[editor.selected()] is not None
        self.layout.operator(
            KOMPASS_OT_slot_fill.bl_idname,
            text="Replace" if filled else "Add",
            icon="VIEWZOOM",
        )
        self.layout.operator(KOMPASS_OT_slot_group.bl_idname, icon="ADD")
        self.layout.operator(KOMPASS_OT_slot_open.bl_idname, text="Open")
        self.layout.menu(KOMPASS_MT_slot_swap.bl_idname)
        self.layout.operator(KOMPASS_OT_slot_clear.bl_idname, text="Remove", icon="X")
