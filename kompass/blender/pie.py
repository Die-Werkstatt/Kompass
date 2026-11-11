# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Opens a stored pie as a native Blender pie menu."""

import bpy

from ..core import model
from . import storage, tools

_ICONS = frozenset(
    bpy.types.UILayout.bl_rna.functions["operator"].parameters["icon"].enum_items.keys()
)


class KOMPASS_OT_pie_open(bpy.types.Operator):
    bl_idname = "kompass.pie_open"
    bl_label = "Open Pie"
    bl_description = "Open a Kompass pie menu"
    # Not in operator search: it is useless without a pie id. Blender wants a
    # plain set here.
    bl_options = {"INTERNAL"}  # noqa: RUF012

    pie: bpy.props.StringProperty(name="Pie", options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context, event):
        pie = _find(self.pie)
        if pie is None:
            self.report({"WARNING"}, f'Kompass has no pie "{self.pie}"')
            return {"CANCELLED"}
        context.window_manager.popup_menu_pie(
            event,
            lambda menu, context: _draw(menu.layout, context, pie),
            title=pie.name,
        )
        return {"FINISHED"}


def _find(pie_id):
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
    icon = slot.icon if slot.icon in _ICONS else "NONE"
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
        target = _find(slot.pie)
        if len(target.slots) > model.NATIVE_SLOTS:
            # Blender's pie menu cannot hold it.
            _draw_unavailable(row, slot.label or target.name)
            return
        button = row.operator(
            KOMPASS_OT_pie_open.bl_idname, text=slot.label or target.name, icon=icon
        )
        button.pie = slot.pie


def _draw_operator(row, slot, icon):
    if operator_type(slot.idname) is None:
        _draw_unavailable(row, slot.label or slot.idname)
        return
    if slot.label is None:
        button = row.operator(slot.idname, icon=icon)
    else:
        button = row.operator(slot.idname, text=slot.label, icon=icon)
    try:
        for name, value in slot.properties.items():
            setattr(button, name, value)
    except (AttributeError, TypeError, ValueError):
        # A setting this Blender does not accept: running the operator with
        # other settings than the stored ones would be worse than not running.
        row.enabled = False


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
