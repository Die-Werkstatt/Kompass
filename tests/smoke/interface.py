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
        'Pie "Broken key" has no shortcut: Blender has no key "NOT_A_KEY"'
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

    def click(x, y):
        editor_window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x - 3, y=y)
        yield PAUSE / 2
        editor_window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y)
        yield PAUSE / 2
        editor_window.event_simulate(type="LEFTMOUSE", value="PRESS", x=x, y=y)
        yield PAUSE / 2
        editor_window.event_simulate(type="LEFTMOUSE", value="RELEASE", x=x, y=y)
        yield PAUSE / 2

    # A click on a tool slot changes nothing; south is the Mesh sub-pie.
    yield from click(x + 2 * FLICK, y)
    assert editor.shown().id == "select"
    yield from click(x, y - 2 * FLICK)
    assert editor.shown().id == "mesh" and editor.in_sub_pie()
    # A click on the dial goes back.
    yield from click(x, y)
    assert editor.shown().id == "select" and not editor.in_sub_pie()

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
