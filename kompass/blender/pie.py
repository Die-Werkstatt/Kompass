# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Opens a stored pie as a native Blender pie menu."""

import bpy

from ..core import model
from . import ADDON, DRAWABLE, storage, tools

# The icons a button can carry, "NONE" first.
ICONS = tuple(
    bpy.types.UILayout.bl_rna.functions["operator"].parameters["icon"].enum_items.keys()
)


# The operator of live.py, which opens a pie as the pie Kompass draws.
LIVE = "kompass.pie_live"


# Why Kompass Native cannot open a pie of 12 slots.
TOO_WIDE = "Kompass Native opens pies of 4 and 8 slots"


def opens(stored):
    """Return whether this edition can open the pie."""
    return DRAWABLE or len(stored.slots) <= model.NATIVE_SLOTS


def drawn(stored):
    """Return whether Kompass draws the pie. Blender's pie menu holds 8 slots."""
    if not DRAWABLE:
        return False
    if len(stored.slots) > model.NATIVE_SLOTS:
        return True
    return bpy.context.preferences.addons[ADDON].preferences.drawn


class KOMPASS_OT_pie_open(bpy.types.Operator):
    bl_idname = "kompass.pie_open"
    bl_label = "Open Pie"
    bl_description = "Open a pie made in Kompass"
    # Not in operator search: it is useless without a pie id. Blender wants a
    # plain set here.
    bl_options = {"INTERNAL"}  # noqa: RUF012

    pie: bpy.props.StringProperty(name="Pie", options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context, event):
        pie = find(self.pie)
        if pie is None:
            self.report({"WARNING"}, f'Kompass has no pie "{self.pie}"')
            return {"CANCELLED"}
        if not opens(pie):
            self.report({"WARNING"}, TOO_WIDE)
            return {"CANCELLED"}
        context.window_manager.popup_menu_pie(
            event,
            lambda menu, context: _draw(menu.layout, context, pie),
            title=pie.name,
        )
        return {"FINISHED"}


def find(pie_id):
    return next((pie for pie in storage.pies if pie.id == pie_id), None)


def _draw(layout, context, pie):
    ring = layout.menu_pie()
    for slot in pie.slots:
        if slot is None:
            # A separator keeps the direction empty and the later slots in place.
            ring.separator()
        else:
            _draw_slot(ring.row(), context, slot)


def _draw_slot(row, context, slot):
    icon = slot.icon if slot.icon in ICONS else "NONE"
    if isinstance(slot, model.ToolSlot):
        label = tools.label(context, slot.space_type, slot.tool)
        if label is None:
            _draw_unavailable(row, slot.label or slot.tool)
            return
        button = row.operator("wm.tool_set_by_id", text=slot.label or label, icon=icon)
        button.name = slot.tool
        button.space_type = slot.space_type
    elif isinstance(slot, model.OperatorSlot):
        _draw_operator(row, slot, icon)
    else:
        target = find(slot.pie)
        if not opens(target):
            _draw_unavailable(row, slot.label or target.name)
            return
        opener = LIVE if drawn(target) else KOMPASS_OT_pie_open.bl_idname
        button = row.operator(opener, text=slot.label or target.name, icon=icon)
        button.pie = slot.pie


def _draw_operator(row, slot, icon):
    if operator_type(slot.idname) is None:
        _draw_unavailable(row, slot.label or slot.idname)
        return
    if slot.label is None:
        button = row.operator(slot.idname, icon=icon)
    else:
        button = row.operator(slot.idname, text=slot.label, icon=icon)
    # Running the operator with other settings than the stored ones would be
    # worse than not running it.
    row.enabled = apply(button, slot.properties)


def apply(settings, properties):
    """Give an operator's settings the stored values. Return whether this
    Blender accepts them all."""
    try:
        for name, value in properties.items():
            known = settings.bl_rna.properties[name]
            # Blender wants a set where a file holds a list.
            flags = getattr(known, "is_enum_flag", False)
            setattr(settings, name, set(value) if flags else value)
    except (AttributeError, KeyError, TypeError, ValueError):
        return False
    return True


def available(context, slot):
    """Return whether what a slot holds can run where context is."""
    if isinstance(slot, model.ToolSlot):
        return tools.label(context, slot.space_type, slot.tool) is not None
    if isinstance(slot, model.OperatorSlot):
        if operator_type(slot.idname) is None:
            return False
        module, _, name = slot.idname.partition(".")
        return getattr(getattr(bpy.ops, module), name).poll()
    return True


def run(context, slot):
    """Do what a tool or operator slot holds. Return whether Blender did."""
    if not available(context, slot):
        return False
    if isinstance(slot, model.ToolSlot):
        bpy.ops.wm.tool_set_by_id(name=slot.tool, space_type=slot.space_type)
        return True
    known = operator_type(slot.idname)
    module, _, name = slot.idname.partition(".")
    try:
        settings = {
            key: set(value)
            if getattr(known.properties[key], "is_enum_flag", 0)
            else value
            for key, value in slot.properties.items()
        }
        getattr(getattr(bpy.ops, module), name)("INVOKE_DEFAULT", **settings)
    # A setting this Blender does not know, or an operator that cannot run
    # where the pointer is.
    except (KeyError, RuntimeError, TypeError, ValueError):
        return False
    return True


def operator_type(idname):
    """Return Blender's description of the operator, or None without it."""
    module, _, name = idname.partition(".")
    try:
        return getattr(getattr(bpy.ops, module), name).get_rna_type()
    except (AttributeError, KeyError):
        return None


def _draw_unavailable(row, text):
    row.enabled = False
    row.label(text=text, icon="ERROR")
