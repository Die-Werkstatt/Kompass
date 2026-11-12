"""The steps of interface.py that open the pie Kompass draws in the 3D Viewport."""

import importlib
import math

import bpy

PAUSE = 1.0


def steps(addon, view3d):
    live = importlib.import_module(addon + ".blender.live")
    layout = importlib.import_module(addon + ".core.layout")
    preferences = bpy.context.preferences.addons[addon].preferences
    window, area = view3d()
    x, y = area.x + area.width // 2, area.y + area.height // 2
    held = {"shift": True, "alt": True}

    def move(x, y, **held):
        window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x - 3, y=y, **held)
        yield PAUSE / 4
        window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y, **held)
        yield PAUSE / 2

    def key(kind, value, x, y, **held):
        window.event_simulate(type=kind, value=value, x=x, y=y, **held)

    def tool():
        tools = bpy.context.workspace.tools
        return tools.from_space_view3d_mode(bpy.context.mode).idname

    # With Kompass Pie on, the keys of the Select pie open the drawn pie.
    # Holding them, moving onto the west slot and letting go picks its tool.
    preferences.drawn = True
    assert tool() == "builtin.select_lasso", tool()
    yield from move(x, y)
    key("Q", "PRESS", x, y, **held)
    yield PAUSE
    assert live._open is not None and live._open.trail[-1].id == "select"
    # It opened under the pointer: the dial showed the disc from the first draw.
    assert live._open.stage.hover_from == 1.0, live._open.stage.hover_from
    yield from move(x - 200, y, **held)
    key("Q", "RELEASE", x - 200, y, **held)
    yield PAUSE
    assert live._open is None
    assert tool() == "builtin.select_box", tool()

    # Keys let go at once leave the pie open. Resting on the south slot
    # opens the Mesh sub-pie around the pointer, Esc goes back, and a click
    # far from every slot closes the pie.
    yield from move(x, y)
    key("Q", "PRESS", x, y, **held)
    key("Q", "RELEASE", x, y, **held)
    yield PAUSE
    assert live._open is not None
    yield from move(x, y - 175)
    yield PAUSE
    assert [pie.id for pie in live._open.trail] == ["select", "mesh"]
    # The pointer rests a few pixels short of where it ends.
    rested = x - area.x, y - 175 - area.y
    assert math.dist(live._open.centres[-1], rested) <= 3, live._open.centres
    # Subdivide cannot run in Object Mode: its slot is disabled and a click
    # on it leaves the pie open.
    mesh = live._open.trail[-1]
    slot = next(
        index
        for index, content in enumerate(mesh.slots)
        if getattr(content, "idname", None) == "mesh.subdivide"
    )
    assert live._open.stage.disabled == {slot}, live._open.stage.disabled
    width = live._open.stage.look.labels[slot][2]
    left, bottom = layout.slot_corner(slot, len(mesh.slots), width)
    scale, centre = live._open.scale, live._open.centres[-1]
    on = (
        round(area.x + centre[0] + (left + width / 2) * scale),
        round(area.y + centre[1] + (bottom + layout.SLOT_HEIGHT / 2) * scale),
    )
    yield from move(*on)
    key("LEFTMOUSE", "PRESS", *on)
    key("LEFTMOUSE", "RELEASE", *on)
    yield PAUSE
    assert [pie.id for pie in live._open.trail] == ["select", "mesh"]
    key("ESC", "PRESS", x, y - 175)
    key("ESC", "RELEASE", x, y - 175)
    yield PAUSE
    assert [pie.id for pie in live._open.trail] == ["select"]
    yield from move(x + 300, y + 150)
    key("LEFTMOUSE", "PRESS", x + 300, y + 150)
    key("LEFTMOUSE", "RELEASE", x + 300, y + 150)
    yield PAUSE
    # It has faded out and is off the editor.
    assert live._open is None and live._closing is None

    # A click on a slot picks it. Right-click closes the pie.
    yield from move(x, y)
    key("Q", "PRESS", x, y, **held)
    key("Q", "RELEASE", x, y, **held)
    yield PAUSE
    yield from move(x + 200, y)
    key("LEFTMOUSE", "PRESS", x + 200, y)
    key("LEFTMOUSE", "RELEASE", x + 200, y)
    yield PAUSE
    assert live._open is None and tool() == "builtin.select_lasso", tool()
    key("Q", "PRESS", x, y, **held)
    key("Q", "RELEASE", x, y, **held)
    yield PAUSE
    assert live._open is not None
    key("RIGHTMOUSE", "PRESS", x, y)
    key("RIGHTMOUSE", "RELEASE", x, y)
    yield PAUSE
    assert live._open is None

    # A pie of 12 slots is drawn whatever the setting says, and Blender's
    # pie menu is back on the Select pie's keys.
    preferences.drawn = False
    key("W", "PRESS", x, y, **held)
    key("W", "RELEASE", x, y, **held)
    yield PAUSE
    assert live._open is not None and len(live._open.trail[-1].slots) == 12
    key("ESC", "PRESS", x, y)
    key("ESC", "RELEASE", x, y)
    yield PAUSE
    assert live._open is None
