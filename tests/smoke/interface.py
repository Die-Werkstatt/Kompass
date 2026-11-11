"""Runs inside Blender with a window, started by run.py --interface.

Presses the pies' shortcuts with simulated events and checks what the chosen
slots did. It cannot check how a pie looks.
"""

import importlib
import os
import sys
import traceback
from dataclasses import replace
from pathlib import Path

import addon_utils
import bpy

PIES = Path(__file__).parent.parent / "data" / "interface.json"
# Seconds Blender gets to handle the events of one step.
PAUSE = 1.0
# Pixels from the pie's centre to where the pointer is released.
FLICK = 120

names = bpy.context.preferences.addons.keys()
(addon,) = [name for name in names if "kompass" in name]
storage = importlib.import_module(addon + ".blender.storage")
keymaps = importlib.import_module(addon + ".blender.keymaps")
editor = importlib.import_module(addon + ".blender.editor")
layout = importlib.import_module(addon + ".core.layout")


def view3d():
    window = bpy.context.window_manager.windows[0]
    area = next(area for area in window.screen.areas if area.type == "VIEW_3D")
    return window, area


def tap(key):
    window, area = view3d()
    x, y = area.x + area.width // 2, area.y + area.height // 2
    window.event_simulate(type=key, value="PRESS", x=x, y=y)
    window.event_simulate(type=key, value="RELEASE", x=x, y=y)


def choose(dx, dy):
    """Hold Shift+Alt+Q at the centre of the 3D Viewport, move, release."""
    window, area = view3d()
    x, y = area.x + area.width // 2, area.y + area.height // 2
    held = {"shift": True, "alt": True}
    window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y)
    yield PAUSE
    window.event_simulate(type="Q", value="PRESS", x=x, y=y, **held)
    yield PAUSE
    x, y = x + dx * FLICK, y + dy * FLICK
    window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y, **held)
    yield PAUSE
    window.event_simulate(type="Q", value="RELEASE", x=x, y=y, **held)
    yield PAUSE


def selected():
    return sorted(ob.name for ob in bpy.context.scene.objects if ob.select_get())


def active_tool():
    return bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname


def steps():
    # Importing binds the shortcuts at once, without a restart.
    assert bpy.ops.kompass.pies_import(filepath=str(PIES)) == {"FINISHED"}
    assert keymaps.problems == [
        'Pie "Broken key" has no shortcut: Blender has no key "NOT_A_KEY"',
        'Pie "Wide" has no shortcut: Blender\'s pie menu holds 8 slots, it has 12',
    ], keymaps.problems

    select = storage.pies[0]
    assert keymaps.text(select.shortcut) == "Shift Alt Q"
    assert keymaps.taken_by(select.shortcut) is None
    frame_all = replace(select.shortcut, key="C", modifiers=frozenset({"shift"}))
    assert keymaps.taken_by(frame_all) == "Frame All", keymaps.taken_by(frame_all)

    # The splash screen of a new profile takes the first key press.
    tap("ESC")
    yield PAUSE
    assert selected() == ["Cube"]

    # North is an operator with a stored setting.
    yield from choose(0, 1)
    assert selected() == ["Camera", "Light"], selected()

    # East is a tool.
    assert active_tool() != "builtin.select_lasso"
    yield from choose(1, 0)
    assert active_tool() == "builtin.select_lasso", active_tool()

    # North-west is an operator that does not exist: nothing happens.
    yield from choose(-1, 1)
    tap("ESC")
    yield PAUSE
    assert selected() == ["Camera", "Light"], selected()

    # South opens the Mesh pie as a sub-pie; its east slot is Shade Smooth.
    cube = bpy.data.objects["Cube"]
    assert not cube.data.polygons[0].use_smooth
    yield from choose(0, -1)
    window, area = view3d()
    x = area.x + area.width // 2 + FLICK
    y = area.y + area.height // 2 - FLICK
    bpy.ops.object.select_all(action="DESELECT")
    cube.select_set(True)
    window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y)
    yield PAUSE
    window.event_simulate(type="LEFTMOUSE", value="PRESS", x=x, y=y)
    window.event_simulate(type="LEFTMOUSE", value="RELEASE", x=x, y=y)
    yield PAUSE
    assert cube.data.polygons[0].use_smooth

    # In Edit Mode the pie of the Mesh keymap opens on the same keys; its
    # west slot subdivides with two cuts.
    bpy.context.view_layer.objects.active = cube
    with bpy.context.temp_override(window=window, area=area):
        bpy.ops.object.mode_set(mode="EDIT")
    yield PAUSE
    yield from choose(-1, 0)
    cube.update_from_editmode()
    assert len(cube.data.vertices) == 56, len(cube.data.vertices)

    # The editor opens in a window of its own and shows the first pie.
    assert bpy.ops.kompass.editor_open() == {"FINISHED"}
    yield PAUSE
    editor_window = bpy.context.window_manager.windows[-1]
    editor_area = editor_window.screen.areas[0]
    assert editor_area.ui_type == "KompassTree", editor_area.ui_type
    assert editor.shown().id == "select"
    canvas = next(r for r in editor_area.regions if r.type == "WINDOW")
    # The pie is centred in what the sidebar leaves of the canvas.
    sidebar = next(r for r in editor_area.regions if r.type == "UI")
    x = canvas.x + (canvas.width - sidebar.width) // 2
    y = canvas.y + canvas.height // 2

    # The pie is drawn smaller where the window is small. The steps below
    # give places in the pie's own lengths, measured from its centre.
    paint = importlib.import_module(addon + ".blender.paint")
    here = {"window": editor_window, "area": editor_area, "region": canvas}
    with bpy.context.temp_override(**here):
        scale = paint.Canvas(bpy.context, 8).scale
    centre = x, y

    def at(x, y):
        return (
            centre[0] + round((x - centre[0]) * scale),
            centre[1] + round((y - centre[1]) * scale),
        )

    def click(x, y):
        x, y = at(x, y)
        editor_window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x - 3, y=y)
        yield PAUSE / 2
        editor_window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y)
        yield PAUSE / 2
        editor_window.event_simulate(type="LEFTMOUSE", value="PRESS", x=x, y=y)
        yield PAUSE / 2
        editor_window.event_simulate(type="LEFTMOUSE", value="RELEASE", x=x, y=y)
        yield PAUSE / 2

    def pick(x, y):
        """Click a slot and close the menu the click opens."""
        yield from click(x, y)
        editor_window.event_simulate(type="ESC", value="PRESS", x=x, y=y)
        editor_window.event_simulate(type="ESC", value="RELEASE", x=x, y=y)
        yield PAUSE / 2

    # A click selects a slot and a click far from every slot selects none.
    # South is the Mesh sub-pie: resting on it opens nothing, Open shows it.
    east, west = layout.BEARINGS.index(90), layout.BEARINGS.index(270)
    mesh = layout.BEARINGS.index(180)
    left, bottom = layout.slot_corner(mesh, 8)
    yield from pick(x + 2 * FLICK, y)
    assert editor.selected() == east, editor.selected()
    assert not bpy.ops.kompass.slot_open.poll()
    yield from click(x + 5 * FLICK // 2, y + 2 * FLICK)
    assert editor.selected() is None, editor.selected()
    yield from pick(x, y + int(bottom) + 10)
    assert editor.shown().id == "select" and editor.selected() == mesh
    assert bpy.ops.kompass.slot_open() == {"FINISHED"}
    assert editor.shown().id == "mesh" and editor.selected() is None
    yield from click(x, y)
    assert editor.shown().id == "select" and editor.selected() == mesh

    # A slot dragged onto another changes places with it.
    before = editor.shown().slots
    for step, value in enumerate(("NOTHING", "PRESS", *["NOTHING"] * 8, "RELEASE")):
        kind = "MOUSEMOVE" if value == "NOTHING" else "LEFTMOUSE"
        along = at(x + 2 * FLICK - min(max(step - 1, 0), 8) * FLICK // 2, y)[0]
        editor_window.event_simulate(type=kind, value=value, x=along, y=y)
        yield PAUSE / 4
    after = editor.shown().slots
    assert (after[west], after[east]) == (before[east], before[west])
    assert editor.selected() == west

    # The selected slot is emptied, filled from the search, and given a new
    # sub-pie.
    assert bpy.ops.kompass.slot_clear() == {"FINISHED"}
    assert editor.shown().slots[west] is None
    assert not bpy.ops.kompass.slot_clear.poll()
    slots = importlib.import_module(addon + ".blender.slots")
    slots._find()
    kinds = {found[0].partition(" ")[0] for found in slots._found}
    assert kinds == {"tool", "operator", "pie"}, kinds
    assert "tool VIEW_3D builtin.select_box" in {found[0] for found in slots._found}
    assert bpy.ops.kompass.slot_fill(found="operator mesh.subdivide") == {"FINISHED"}
    assert editor.shown().slots[west].idname == "mesh.subdivide"
    count = len(storage.pies)
    assert bpy.ops.kompass.slot_group() == {"FINISHED"}
    assert len(storage.pies) == count + 1
    assert editor.shown().slots[west].pie == storage.pies[-1].id == "sub-pie"
    assert bpy.ops.kompass.slot_fill(found="operator mesh.subdivide") == {"FINISHED"}

    # The slot takes a label and loses it for an empty one.
    assert bpy.ops.kompass.slot_label(label=" Cut ") == {"FINISHED"}
    assert editor.shown().slots[west].label == "Cut"
    assert bpy.ops.kompass.slot_label(label="") == {"FINISHED"}
    assert editor.shown().slots[west].label is None

    # Settings shows the operator's settings on a keymap item that no key
    # reaches. OK stores the ones that were set and removes the item.
    with bpy.context.temp_override(**here):
        bpy.ops.kompass.slot_settings("INVOKE_DEFAULT")
    yield PAUSE
    keymap, item = slots.KOMPASS_OT_slot_settings._item
    held = len(keymap.keymap_items)
    item.properties.number_cuts = 3
    editor_window.event_simulate(type="RET", value="PRESS")
    editor_window.event_simulate(type="RET", value="RELEASE")
    yield PAUSE
    assert editor.shown().slots[west].properties == {"number_cuts": 3}
    assert len(keymap.keymap_items) == held - 1

    # Every context the editor offers is a keymap of Blender's.
    default = bpy.context.window_manager.keyconfigs.default.keymaps
    for keymap, space_type, _ in keymaps.CONTEXTS:
        assert default[keymap].space_type == space_type, keymap

    # The next key press becomes the shortcut and is bound at once. Esc
    # keeps the old one.
    def press(key, **held):
        with bpy.context.temp_override(**here):
            bpy.ops.kompass.pie_shortcut("INVOKE_DEFAULT")
        yield PAUSE / 2
        editor_window.event_simulate(type=key, value="PRESS", x=x, y=y, **held)
        editor_window.event_simulate(type=key, value="RELEASE", x=x, y=y, **held)
        yield PAUSE / 2

    yield from press("C", shift=True)
    bound = editor.shown().shortcut
    assert (bound.key, bound.modifiers) == ("C", {"shift"}), bound
    assert (bound.keymap, bound.space_type) == ("3D View", "VIEW_3D")
    assert keymaps.warnings(editor.shown()) == ['Blender also has "Frame All" on it']
    assert any(item.type == "C" for _, item in keymaps._items)
    yield from press("ESC")
    assert editor.shown().shortcut == bound
    assert bpy.ops.kompass.pie_context(keymap="Mesh") == {"FINISHED"}
    assert editor.shown().shortcut == replace(bound, keymap="Mesh", space_type="EMPTY")
    assert bpy.ops.kompass.pie_unbind() == {"FINISHED"}
    assert editor.shown().shortcut is None
    assert not any(item.type == "C" for _, item in keymaps._items)
    yield from press("Q", shift=True, alt=True)
    assert editor.shown().shortcut == select.shortcut

    # In preview a click selects nothing. A click on a tool slot changes
    # nothing, a click far below Mesh does nothing, a click just below its
    # box opens it.
    assert bpy.ops.kompass.editor_preview() == {"FINISHED"}
    assert editor.selected() is None
    yield from click(x + 2 * FLICK, y)
    assert editor.shown().id == "select" and editor.selected() is None
    yield from click(x, y - 2 * FLICK)
    assert editor.shown().id == "select"
    yield from click(x, y + int(bottom) - 12)
    assert editor.shown().id == "mesh" and editor.in_sub_pie()
    # A click on the dial goes back.
    yield from click(x, y)
    assert editor.shown().id == "select" and not editor.in_sub_pie()

    # Resting on the Mesh slot opens it without a click. Mesh has a sub-pie
    # in the same slot, which stays shut until the pointer has left it.
    south = at(x + int(left) + layout.SLOT_WIDTH // 2, y + int(bottom) + 10)
    editor_window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y)
    yield PAUSE / 2
    editor_window.event_simulate(
        type="MOUSEMOVE", value="NOTHING", **dict(zip("xy", south))
    )
    yield PAUSE
    assert editor.shown().id == "mesh" and editor.depth() == 2, editor.shown().id
    editor_window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y)
    yield PAUSE / 2
    editor_window.event_simulate(
        type="MOUSEMOVE", value="NOTHING", **dict(zip("xy", south))
    )
    yield PAUSE
    assert editor.shown().id == "broken" and editor.depth() == 3, editor.shown().id
    yield from click(x, y)
    yield from click(x, y)
    assert editor.shown().id == "select" and editor.depth() == 1

    # A pointer that leaves the canvas before the delay is over opens nothing.
    editor_window.event_simulate(
        type="MOUSEMOVE", value="NOTHING", **dict(zip("xy", south))
    )
    editor_window.event_simulate(
        type="MOUSEMOVE", value="NOTHING", x=sidebar.x + sidebar.width // 2, y=y
    )
    yield PAUSE
    assert editor.shown().id == "select", editor.shown().id

    # With Blender's Reduce Motion the pie still opens after the delay.
    bpy.context.preferences.view.use_reduce_motion = True
    editor_window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y)
    yield PAUSE / 2
    editor_window.event_simulate(
        type="MOUSEMOVE", value="NOTHING", **dict(zip("xy", south))
    )
    yield PAUSE
    assert editor.shown().id == "mesh", editor.shown().id

    # A pie of 12 slots: its second slot, a sub-pie, lies at 42 degrees. A
    # pie of 8 has nothing there. The click is just above the slot's box.
    assert bpy.ops.kompass.editor_show(pie="wide") == {"FINISHED"}
    yield PAUSE / 2
    left, bottom = layout.slot_corner(1, 12)
    yield from click(x + int(left) + 60, y + int(bottom) + layout.SLOT_HEIGHT + 10)
    assert editor.shown().id == "broken" and editor.depth() == 2, editor.shown().id

    # Disabling with the editor open leaves nothing registered.
    addon_utils.disable(addon)
    assert not editor.KompassTree.is_registered
    left = [
        item.idname
        for keymap in bpy.context.window_manager.keyconfigs.addon.keymaps
        for item in keymap.keymap_items
        if item.idname.startswith("kompass.")
    ]
    assert left == [], left
    assert not hasattr(bpy.types, "KOMPASS_OT_pie_open")


RUN = steps()


def tick():
    try:
        return next(RUN)
    except StopIteration:
        print("Kompass interface test passed")
        code = 0
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        code = 1
    sys.stdout.flush()
    sys.stderr.flush()
    # A timer cannot set Blender's exit code any other way.
    os._exit(code)


bpy.app.timers.register(tick, first_interval=3.0)
