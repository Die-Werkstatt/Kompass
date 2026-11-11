# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""The Kompass editor: an editor type of its own that shows one pie."""

import bpy

from ..core import edit, model
from . import keymaps, storage

# The pie on the canvas is the last of these ids; before it, the pies whose
# sub-pie slots led there.
_trail = []
# The id of a pie and the index of its selected slot.
_selected = None
# In preview a click selects nothing and the pie behaves as it will when open.
preview = False


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


def depth():
    """Return how many pies deep the canvas is: 1 for a pie, 2 for its sub-pie."""
    return len(_trail) if _trail and shown().id == _trail[-1] else 1


def in_sub_pie():
    return depth() > 1


def selected():
    """Return the selected slot of the pie on the canvas, or None."""
    pie = shown()
    if pie is None or _selected is None or _selected[0] != pie.id:
        return None
    return _selected[1]


def select(slot):
    """Select that slot of the pie on the canvas, or none for None."""
    global _selected
    _selected = None if slot is None else (shown().id, slot)


class KOMPASS_OT_editor_open(bpy.types.Operator):
    """Open the Kompass editor in a new window"""

    bl_idname = "kompass.editor_open"
    bl_label = "Open Editor"

    def execute(self, context):
        manager = context.window_manager
        # wm.window_new() gives a window as large as the main one and takes
        # no size. The Info Log opens in a small window of its own.
        with context.temp_override(window=manager.windows[0]):
            bpy.ops.screen.info_log_show()
        area = manager.windows[-1].screen.areas[0]
        area.ui_type = KompassTree.bl_idname
        space = area.spaces.active
        # Blender draws gizmos in a node editor only when it shows a tree.
        space.node_tree = _tree()
        space.show_region_header = False
        space.show_region_ui = True
        bpy.app.timers.register(_show_tab, first_interval=0.1)
        return {"FINISHED"}


def _show_tab():
    """Bring the Kompass tab to the front of each editor's sidebar."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.ui_type != KompassTree.bl_idname:
                continue
            sidebar = next(region for region in area.regions if region.type == "UI")
            try:
                sidebar.active_panel_category = KOMPASS_PT_pies.bl_category
            except AttributeError:
                # Blender lets it be set once the sidebar has been drawn.
                return 0.1
    return None


def _tree():
    for tree in bpy.data.node_groups:
        if tree.bl_idname == KompassTree.bl_idname:
            return tree
    return bpy.data.node_groups.new(KompassTree.bl_label, KompassTree.bl_idname)


def redraw(context):
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
        redraw(context)
        return {"FINISHED"}


def enter(slot):
    """Show the sub-pie in that slot of the pie on the canvas."""
    pie = shown()
    _trail[:] = [*(_trail or [pie.id]), pie.slots[slot].pie]


def click(slot):
    """Take a click on a slot, on the dial for -1, or on neither for None.

    The dial goes back. In preview a slot opens its sub-pie. Otherwise it is
    selected and shows its menu.
    """
    pie = shown()
    if pie is None:
        return
    if slot is not None and slot < 0:
        if in_sub_pie():
            _trail.pop()
    elif not preview:
        select(slot)
        if slot is not None:
            bpy.ops.wm.call_menu(name="KOMPASS_MT_slot")
    elif slot is not None and isinstance(pie.slots[slot], model.SubPieSlot):
        enter(slot)


class KOMPASS_OT_editor_preview(bpy.types.Operator):
    """Open sub-pies on hover instead of selecting slots"""

    bl_idname = "kompass.editor_preview"
    bl_label = "Preview"
    bl_options = {"INTERNAL"}  # noqa: RUF012

    def execute(self, context):
        global preview
        preview = not preview
        select(None)
        redraw(context)
        return {"FINISHED"}


class Edit:
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
        redraw(context)
        return {"FINISHED"}


class KOMPASS_OT_pie_add(Edit, bpy.types.Operator):
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


class KOMPASS_OT_pie_rename(Edit, bpy.types.Operator):
    """Change the name of the pie on the canvas"""

    bl_idname = "kompass.pie_rename"
    bl_label = "Rename Pie"

    name: bpy.props.StringProperty(name="Name")

    def invoke(self, context, _event):
        self.name = shown().name
        return context.window_manager.invoke_props_dialog(self)

    def edited(self, pies, pie):
        return edit.rename(pies, pie.id, self.name.strip())


class KOMPASS_OT_pie_duplicate(Edit, bpy.types.Operator):
    """Copy the pie on the canvas without its shortcut"""

    bl_idname = "kompass.pie_duplicate"
    bl_label = "Duplicate Pie"

    def edited(self, pies, pie):
        pies = edit.duplicate(pies, pie.id)
        _trail[:] = [pies[pies.index(pie) + 1].id]
        return pies


class KOMPASS_OT_pie_delete(Edit, bpy.types.Operator):
    """Delete the pie on the canvas and empty the slots that open it"""

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
        self.layout.operator(
            KOMPASS_OT_editor_preview.bl_idname, icon="PLAY", depress=preview
        )
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
