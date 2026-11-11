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

- [ ] Preferences > Add-ons > Kompass > Open Editor: a new window opens with
      the Select pie on a dark canvas. In its sidebar (N), the Kompass tab
      lists the pies.
- [ ] Move the pointer around the dial: the needle and the outer arrow
      follow it, and the nearest slot lights up red, stronger further out.
- [ ] Click MESH: the Mesh pie replaces it, with a smaller dial and BACK
      below. Click the dial: Select is back.
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
