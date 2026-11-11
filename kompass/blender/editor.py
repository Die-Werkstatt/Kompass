# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""The Kompass editor: an editor type of its own that shows one pie."""

import bpy

from ..core import model
from . import storage

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


class KOMPASS_OT_editor_show(bpy.types.Operator):
    """Show this pie on the canvas"""

    bl_idname = "kompass.editor_show"
    bl_label = "Show Pie"
    bl_options = {"INTERNAL"}  # noqa: RUF012

    pie: bpy.props.StringProperty()

    def execute(self, context):
        _trail[:] = [self.pie]
        context.area.tag_redraw()
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


class KOMPASS_PT_pies(bpy.types.Panel):
    bl_label = "Pies"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Kompass"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == KompassTree.bl_idname

    def draw(self, _context):
        column = self.layout.column(align=True)
        on_canvas = shown()
        for pie in storage.pies:
            button = column.operator(
                KOMPASS_OT_editor_show.bl_idname,
                text=pie.name,
                depress=pie is on_canvas,
            )
            button.pie = pie.id
