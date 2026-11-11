# Manual test

What only a person can judge. Run it once per supported Blender version
before a release, on each operating system you have. Everything else is
covered by `python3 .claude/suite-check.py`.

## Set up

Install Kompass and import `tests/data/example.json` as the
[README](../README.md#install-from-source) describes.

## The pie

In the 3D Viewport, in Object Mode, with the default cube selected.

- [ ] Hold Shift+Alt+Q: the Select pie opens under the pointer with Box
      Select to the west, Lasso to the east, Mesh to the south and Invert to
      the north.
- [ ] Hold, flick north, release: the selection inverts. It works at the
      speed you would use it at.
- [ ] Hold, flick east, release: the active tool is Select Lasso.
- [ ] Tap Shift+Alt+Q and let go: the pie stays open, and a click on an
      entry runs it.
- [ ] Open the pie and press Esc or the right mouse button: it closes and
      nothing changes.
- [ ] Flick south: the Mesh pie opens at the pointer. Subdivide is greyed
      out in Object Mode.
- [ ] In Edit Mode, flick south and click Subdivide: every edge gets two
      cuts.
- [ ] The pie is readable over a busy scene and near each edge of the
      viewport.

## Looks

- [ ] Repeat "Hold Shift+Alt+Q" with Preferences > Interface > Resolution
      Scale at 2.0: nothing is clipped or overlaps.
- [ ] Repeat it with the Blender Light theme: labels and icons are readable.

## Editor

- [ ] Preferences > Add-ons > Kompass > Open Editor: a small new window opens
      with the Select pie on a black canvas. Its sidebar shows the Kompass
      tab, which lists the pies.
- [ ] Move the pointer around the dial: the needle and the outer arrow
      follow it, and the nearest slot lights up red, stronger further out.
- [ ] Move the pointer into the dial: the needle turns into a red disc with
      a white border, the long ticks shorten and the outer arrow fades. Move
      out: it turns back.
- [ ] Click LASSO: it gets a white outline and a menu opens beside it. Click
      far from every slot: the outline is gone.
- [ ] Rest the pointer on MESH: nothing opens. Click it and choose Open: the
      Mesh pie shows. Click the dial: Select is back, MESH still outlined.
- [ ] Press SELECT BOX, move to LASSO and release: a SELECT BOX box follows
      the pointer, LASSO is outlined red, and the two change places. Drag a
      slot onto an empty one: it moves there. Release far from every slot:
      nothing changes.
- [ ] Click a slot, Replace, type "subdiv", pick Subdivide (mesh.subdivide):
      the slot reads SUBDIVIDE. Click an empty slot: the menu says Add.
- [ ] Slots 12: the pie has 12 slots and every filled slot is where it was.
      Slots 8: it has 8 again. With something in slot 3 of the 12, Slots 8
      reports that slot 3 has no place and changes nothing.
- [ ] Click a slot, New Sub-Pie: the slot reads SUB-PIE with a red corner and
      the pie list has a Sub-Pie. Click a slot, Remove: it is empty.
- [ ] Click a filled slot, Label, type a name, OK: the slot reads that name.
      Label again with an empty field: it reads Blender's name.
- [ ] Click a filled slot, Icon, search and choose one: Blender's pie shows it
      beside the slot's name. Icon again, None: it is gone.
- [ ] Click a slot that holds an operator, Settings: Blender's settings for the
      operator show. Change one, OK, open the pie on its shortcut and choose
      the slot: the operator runs with that setting.
- [ ] Close and reopen Blender: the changes are still there.
- [ ] In the 3D Viewport, Shift+Alt+Q: the pie shows the new slots.
- [ ] In the Shortcut panel click the shortcut and press Shift+C: the button
      reads Shift C and a line says Blender also has "Frame All" on it. Click
      it and press Esc: it stays. Choose Mesh Edit Mode below it. Press the X:
      the button reads Set Shortcut. Set Shift+Alt+Q again.
- [ ] Turn on Preview in the Kompass tab for the steps up to Reduce Motion:
      a click outlines nothing and opens no menu.
- [ ] MESH has a grey outline and lights up grey, not red. Rest the pointer
      on it: red fills it downward and the Mesh pie opens, with a smaller
      dial and BACK below. Select fades and shrinks while Mesh fades in.
- [ ] Click the dial: Mesh shrinks away and Select is back.
- [ ] Move the pointer from the dial toward MESH: the slot stays dark until
      the pointer is close to it. Click far from it: nothing happens. Click
      just beside the slot, without resting on it: Mesh opens.
- [ ] Rename a pie that is a sub-pie to a name of 40 letters and show its
      parent: the slot is wider than the others and the name is cut off.
      Point at it from the dial's edge: after a moment the name slides left
      to its end. Point elsewhere: it slides back.
- [ ] Move onto MESH and straight off the canvas onto the sidebar: Select
      stays.
- [ ] Preferences > Interface > Reduce Motion on: the same steps work
      without any fading or growing. Turn it off again.
- [ ] In the Kompass tab, New adds a pie named Pie and shows it. Rename it,
      duplicate it, delete the copy: the list follows each step, and Delete
      asks first.
- [ ] Delete Mesh, then show Select: its south slot is empty.
- [ ] Make the window small: the pie shrinks to fit and stays clickable.
- [ ] Scroll and middle-drag on the canvas: nothing moves.
- [ ] Save the `.blend`, reopen it: the editor window is back and works.
- [ ] Disable Kompass with the editor open: no error.

## Export and import

- [ ] Export All opens the file browser with the name `kompass-pies.json`.
- [ ] Exporting over an existing file asks before it overwrites.
- [ ] Import shows Replace My Pies in the file browser's side panel, and it
      is off each time.
- [ ] Import the exported file: the list shows Select and Mesh twice, and
      Blender reports that another pie has the shortcut of "Select".
- [ ] Import it again with Replace My Pies on: the list does not grow.
- [ ] Import a file that is not a pie file, such as `pyproject.toml` renamed
      to `.json`: Blender reports "Nothing was imported" with the reason, and
      the list is unchanged.

## Shortcuts

- [ ] Preferences > Keymap, search by name for "Open Pie": one item per pie
      that has a shortcut.
- [ ] Disable Kompass: the items are gone and Shift+Alt+Q does nothing.
- [ ] Enable it again: the pies and their shortcuts are back.
- [ ] Restart Blender: the pies and their shortcuts are still there.
