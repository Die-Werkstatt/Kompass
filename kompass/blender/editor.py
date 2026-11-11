# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""The Kompass editor: an editor type of its own that shows one pie."""

import bpy

from ..core import edit, model
from . import keymaps, storage

# The pie on the canvas is the last of these ids; before it, the pies whose
# sub-pie slots led there.
_trail = []


class KompassTree(bpy.types.NodeTree):
    """Makes Kompass an entry in Blender's editor-type menu. It holds no nodes"""

    bl_idname = "KompassTree"
    bl_label = "Kompass"
    bl_icon = "ORIENTATION_GIMBAL"


def shown():
    """Return the pie on the canvas, or None when there are no pies."""
    by_id = {pie.id: pie for pie in storage.pies}
    if _trail and _trail[-1] in by_id:
        return by_id[_trail[-1]]
    return storage.pies[0] if storage.pies else None


def in_sub_pie():
    return len(_trail) > 1 and shown().id == _trail[-1]


class KOMPASS_OT_editor_open(bpy.types.Operator):
    """Open the Kompass editor in a new window"""

    bl_idname = "kompass.editor_open"
    bl_label = "Open Editor"

    def execute(self, context):
        manager = context.window_manager
        # From the Preferences window Blender would copy that window.
        with context.temp_override(window=manager.windows[0]):
            bpy.ops.wm.window_new()
        area = manager.windows[-1].screen.areas[0]
        area.ui_type = KompassTree.bl_idname
        space = area.spaces.active
        # Blender draws gizmos in a node editor only when it shows a tree.
        space.node_tree = _tree()
        space.show_region_header = False
        space.show_region_ui = True
        return {"FINISHED"}


def _tree():
    for tree in bpy.data.node_groups:
        if tree.bl_idname == KompassTree.bl_idname:
            return tree
    return bpy.data.node_groups.new(KompassTree.bl_label, KompassTree.bl_idname)


def _redraw(context):
    """Redraw every Kompass editor. The pie list is drawn in each."""
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.ui_type == KompassTree.bl_idname:
                area.tag_redraw()


class KOMPASS_OT_editor_show(bpy.types.Operator):
    """Show this pie on the canvas"""

    bl_idname = "kompass.editor_show"
    bl_label = "Show Pie"
    bl_options = {"INTERNAL"}  # noqa: RUF012

    pie: bpy.props.StringProperty()

    def execute(self, context):
        _trail[:] = [self.pie]
        _redraw(context)
        return {"FINISHED"}


def click(slot):
    """Open the sub-pie in the slot, or go back for -1, the dial."""
    pie = shown()
    if pie is None:
        return
    if slot < 0:
        if in_sub_pie():
            _trail.pop()
    elif isinstance(pie.slots[slot], model.SubPieSlot):
        _trail[:] = [*(_trail or [pie.id]), pie.slots[slot].pie]


class _Edit:
    """An operator that changes the stored pies."""

    bl_options = {"INTERNAL"}  # noqa: RUF012

    @classmethod
    def poll(cls, _context):
        return shown() is not None

    def execute(self, context):
        try:
            keymaps.store(self.edited(storage.pies, shown()))
        # InvalidPieFile, for an empty name, is a ValueError.
        except (OSError, ValueError) as error:
            self.report({"ERROR"}, f"Nothing was changed: {error}")
            return {"CANCELLED"}
        _redraw(context)
        return {"FINISHED"}


class KOMPASS_OT_pie_add(_Edit, bpy.types.Operator):
    """Add an empty pie"""

    bl_idname = "kompass.pie_add"
    bl_label = "New Pie"

    @classmethod
    def poll(cls, _context):
        return True

    def edited(self, pies, _pie):
        pies = edit.add(pies, "Pie")
        _trail[:] = [pies[-1].id]
        return pies


class KOMPASS_OT_pie_rename(_Edit, bpy.types.Operator):
    """Give the pie on the canvas another name"""

    bl_idname = "kompass.pie_rename"
    bl_label = "Rename Pie"

    name: bpy.props.StringProperty(name="Name")

    def invoke(self, context, _event):
        self.name = shown().name
        return context.window_manager.invoke_props_dialog(self)

    def edited(self, pies, pie):
        return edit.rename(pies, pie.id, self.name.strip())


class KOMPASS_OT_pie_duplicate(_Edit, bpy.types.Operator):
    """Copy the pie on the canvas. The copy has no shortcut"""

    bl_idname = "kompass.pie_duplicate"
    bl_label = "Duplicate Pie"

    def edited(self, pies, pie):
        pies = edit.duplicate(pies, pie.id)
        _trail[:] = [pies[pies.index(pie) + 1].id]
        return pies


class KOMPASS_OT_pie_delete(_Edit, bpy.types.Operator):
    """Delete the pie on the canvas. Slots that open it become empty"""

    bl_idname = "kompass.pie_delete"
    bl_label = "Delete Pie"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def edited(self, pies, pie):
        return edit.delete(pies, pie.id)


class KOMPASS_PT_pies(bpy.types.Panel):
    bl_label = "Pies"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Kompass"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == KompassTree.bl_idname

    def draw(self, _context):
        row = self.layout.row(align=True)
        row.operator(KOMPASS_OT_pie_add.bl_idname, text="New", icon="ADD")
        row.operator(KOMPASS_OT_pie_duplicate.bl_idname, text="", icon="DUPLICATE")
        row.operator(KOMPASS_OT_pie_rename.bl_idname, text="", icon="GREASEPENCIL")
        row.operator(KOMPASS_OT_pie_delete.bl_idname, text="", icon="TRASH")
        column = self.layout.column(align=True)
        on_canvas = shown()
        for pie in storage.pies:
            button = column.operator(
                KOMPASS_OT_editor_show.bl_idname,
                text=pie.name,
                depress=pie is on_canvas,
            )
            button.pie = pie.id
