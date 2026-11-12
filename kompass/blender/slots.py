# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""What the editor does with the selected slot."""

from dataclasses import replace

import bpy

from ..core import edit, model
from . import editor, paint, pie, storage, tools


def _names(pie):
    """Return what a menu calls each slot: where it is and what it holds."""
    return [
        f"{model.slot_name(pie, slot)}: {text.title() or 'Empty'}"
        for slot, (text, _, _) in enumerate(paint.labels(pie))
    ]


def _held():
    """Return what the selected slot holds, or None."""
    slot = editor.selected()
    return None if slot is None else editor.shown().slots[slot]


class KOMPASS_OT_slot_clear(editor.Edit, bpy.types.Operator):
    """Empty the selected slot"""

    bl_idname = "kompass.slot_clear"
    bl_label = "Clear Slot"

    @classmethod
    def poll(cls, _context):
        return _held() is not None

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
    """Search for a tool, operator or pie to put in the selected slot"""

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
    """Add a pie that the selected slot opens as a sub-pie"""

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
        return isinstance(_held(), model.SubPieSlot)

    def execute(self, context):
        editor.enter(editor.selected())
        editor.redraw(context)
        return {"FINISHED"}


class KOMPASS_OT_slot_label(editor.Edit, bpy.types.Operator):
    """Name the selected slot, or leave empty for Blender's name"""

    bl_idname = "kompass.slot_label"
    bl_label = "Slot Label"

    label: bpy.props.StringProperty(name="Label")

    @classmethod
    def poll(cls, _context):
        return _held() is not None

    def invoke(self, context, _event):
        self.label = _held().label or ""
        return context.window_manager.invoke_props_dialog(self)

    def edited(self, pies, pie):
        content = replace(_held(), label=self.label.strip() or None)
        return edit.place(pies, pie.id, editor.selected(), content)


_ICONS = [
    (name, name.replace("_", " ").title(), "", name, number)
    for number, name in enumerate(pie.ICONS)
]


class KOMPASS_OT_slot_icon(editor.Edit, bpy.types.Operator):
    """Search for an icon of Blender's to show beside the selected slot's name"""

    bl_idname = "kompass.slot_icon"
    bl_label = "Slot Icon"
    bl_property = "icon"

    icon: bpy.props.EnumProperty(items=_ICONS)

    @classmethod
    def poll(cls, _context):
        return _held() is not None

    def invoke(self, context, _event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}

    def edited(self, pies, pie):
        content = replace(_held(), icon=None if self.icon == "NONE" else self.icon)
        return edit.place(pies, pie.id, editor.selected(), content)


def _plain(value):
    """Return a setting of Blender's as what a pie file holds."""
    if isinstance(value, (bool, int, float, str)):
        return value
    # A set of flags has no order of its own.
    return [
        _plain(item) for item in (sorted(value) if isinstance(value, set) else value)
    ]


class KOMPASS_OT_slot_settings(editor.Edit, bpy.types.Operator):
    """Change the settings the operator in the selected slot runs with"""

    bl_idname = "kompass.slot_settings"
    bl_label = "Operator Settings"

    # Blender draws an operator's settings for a keymap item only, so the
    # dialog edits one that no key reaches.
    _item = None

    @classmethod
    def poll(cls, context):
        held = _held()
        return (
            isinstance(held, model.OperatorSlot)
            and pie.operator_type(held.idname) is not None
            and context.window_manager.keyconfigs.addon is not None
        )

    def invoke(self, context, _event):
        keyconfig = context.window_manager.keyconfigs.addon
        keymap = keyconfig.keymaps.new(name="Window", space_type="EMPTY")
        item = keymap.keymap_items.new(_held().idname, "NONE", "PRESS")
        item.active = False
        pie.apply(item.properties, _held().properties)
        KOMPASS_OT_slot_settings._item = keymap, item
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context):
        self.layout.template_keymap_item_properties(self._item[1])

    def edited(self, pies, pie):
        settings = self._item[1].properties
        properties = {
            known.identifier: _plain(getattr(settings, known.identifier))
            for known in settings.bl_rna.properties
            if known.identifier != "rna_type"
            and settings.is_property_set(known.identifier)
        }
        self.cancel(None)
        content = replace(_held(), properties=properties)
        return edit.place(pies, pie.id, editor.selected(), content)

    def cancel(self, _context):
        keymap, item = self._item
        keymap.keymap_items.remove(item)


class KOMPASS_OT_slot_swap(editor.Edit, bpy.types.Operator):
    """Exchange the contents of the selected slot and this slot of the pie on the canvas"""

    bl_idname = "kompass.slot_swap"
    bl_label = "Swap Slots"

    other: bpy.props.IntProperty()

    @classmethod
    def poll(cls, _context):
        return editor.selection() is not None

    def edited(self, pies, pie):
        # A slot dragged into a sub-pie is selected in the pie it came from.
        slot = editor.selection()
        # The selection stays with what was selected.
        editor.select(self.other)
        return edit.swap(pies, slot, (pie.id, self.other))


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
        # A menu opened by wm.call_menu executes its operators: without this
        # the search and the dialogs never show.
        self.layout.operator_context = "INVOKE_DEFAULT"
        self.layout.operator(
            KOMPASS_OT_slot_fill.bl_idname,
            text="Add" if _held() is None else "Replace",
            icon="VIEWZOOM",
        )
        self.layout.operator(KOMPASS_OT_slot_group.bl_idname, icon="ADD")
        self.layout.operator(KOMPASS_OT_slot_open.bl_idname, text="Open")
        self.layout.operator(KOMPASS_OT_slot_label.bl_idname, text="Label...")
        self.layout.operator(KOMPASS_OT_slot_icon.bl_idname, text="Icon...")
        self.layout.operator(KOMPASS_OT_slot_settings.bl_idname, text="Settings...")
        self.layout.menu(KOMPASS_MT_slot_swap.bl_idname)
        self.layout.operator(KOMPASS_OT_slot_clear.bl_idname, text="Remove", icon="X")
