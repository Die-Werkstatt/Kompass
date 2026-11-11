# Kompass interface design

How the pie looks and behaves on the Kompass editor canvas.
[`pie-playground.html`](pie-playground.html) is a working mock-up: open it in a browser.
Variant **G · Bearing needle** is the chosen design; D, E and F stay in the file for comparison.
[`pie-motion.html`](pie-motion.html) adds the centre hover state and the motion below to variant G.

Blender draws the live pie menu itself, in the user's theme.
Everything below applies to the editor canvas, which Kompass draws with `gpu` and `blf`.

## Look

| Part | Value |
|---|---|
| Slot labels | Barlow SemiBold, capitals, tracking 0.08 em |
| Slots | square corners; ground `#0E0E0E`, outline `#2C2C2C` |
| Slot placement | one rule for every slot count and width: the box sits on the ring at its bearing, then moves out by half its width times the bearing's sine and half its height times its cosine |
| 8 slots | bearings every 45°, ring 150 px |
| 12 slots | bearings 0°, 42°, 68°, 90°, 112°, 138°, 180°, 222°, 248°, 270°, 292°, 318°, ring 170 px: every pair of 120 px neighbours is 37 px apart. Equal 30° steps would leave about 15 px near north and south and 81 px near east and west, because wide boxes sit side by side there and stack here |
| Slot width | at least 120 px; grows to fit the label plus 12 px padding each side, up to 180 px |
| Long label | clipped at the padding |
| Sub-pie marker | signal-red triangle in a slot's top-right corner |
| Sub-pie slot | outline `#5A5955`; grey highlight `#4A4946` instead of signal red |
| Centre dial | ring with a tick every 5°, longer every 45°, and the split compass needle |
| Outer arrow | signal-red triangle outside the ring; turns with the needle |
| Centre hover | the needle becomes a signal-red disc with a 3 px white border, radius 75% of the needle length; the 45° ticks shorten to the length of the 5° ticks; the outer arrow slides in onto the ring, shrinks and fades; the ring stays |
| Sub-pie dial | 72% of the main dial |
| Sub-pie title | pie name in capitals above the dial |
| Dial label | BACK in a sub-pie, CLOSE at the root, below the dial |
| Colours | see [`../brand/README.md`](../brand/README.md) |

`kompass/blender/paint.py` draws the slots, the dial, the needle, the outer arrow, the sub-pie title and the dial label.
It differs from the table above in the font, which is Blender's interface font without tracking, because `blf` has no letter spacing and the font is undecided (#10).

## Behaviour

| Event | Result |
|---|---|
| Pointer moves | needle and outer arrow follow it; easing time constant 45 ms, shortest arc |
| Pointer within 8 px of the centre | needle holds its last heading |
| Pointer outside the dial ring | the slot with the nearest bearing is selected; with 12 slots the slices near east and west are narrower |
| Pointer inside the dial ring | no slot is selected; the dial turns to its hover state in 120 ms, ease-in-out cubic |
| Pointer leaves the dial ring | the hover state reverses from wherever it is |
| Highlight on a tool slot | signal red, strength rises with distance past the ring and closeness to the needle; the selected slot keeps at least 30% |
| Highlight on a sub-pie slot | the same strength in grey |
| Pointer rests on a sub-pie slot | signal red fills the slot away from the centre over 100 ms and its outline turns red: east slots fill left to right, west right to left, north upward, south downward, other slots along the stronger axis of their bearing, so 42° fills upward and 45° and 68° sideways |
| The fill completes | the sub-pie opens, centred on the pointer |
| Pointer rests on a slot with a clipped label | after 400 ms the label slides left at 40 px/s until its end shows |
| Pointer leaves that slot | the label eases back, time constant 60 ms |
| Pie opens | every part fades in over 120 ms, ease-out cubic; slots and labels move out from 88% of their distance to the centre; the dial grows from 92% |
| Pie closes | the same, reversed; the dial keeps its state, so a pie closed from the centre fades out as the disc and the needle does not return |
| Click on a tool slot | runs the tool and closes the pie |
| Press, drag over 250 ms, release on a slot | same as a click |
| Click on the dial, Esc or right-click | back one level; closes the pie at the root |
| Click neither on the dial nor within 24 px of a slot | closes the pie; native Blender pies pick by direction at any distance instead (Sandro, 11 Nov 2026) |
| Return from a sub-pie | the slot that opened it does not reopen until the pointer leaves it |
| Opening a sub-pie | the needle keeps its heading; it does not reset to north |
| Opening a sub-pie | the parent pie fades and shrinks to 90% around the pointer while the sub-pie opens, both in 120 ms |
| Back from a sub-pie | the sub-pie fades and shrinks to 88% around its centre while the parent opens |
| Reduced motion | every change is immediate |

On the canvas today: the highlight and the selection by bearing, the centre hover state, slot width and long labels, the fill on sub-pie slots, opening a sub-pie on hover or by a click, the opening motion and both sub-pie handoffs work as above.
A sub-pie left through its centre fades out as the disc.
The needle and arrow follow the pointer without easing.
A sub-pie opens in the middle of the canvas, not on the pointer.
A slot that is under the pointer when its pie arrives does not open until the pointer has left it.
Reduced motion is Blender's Preferences > Interface > Reduce Motion; the 100 ms before a sub-pie opens stay.
With it a long label jumps to its end after the 400 ms.
Not on the canvas: the closing motion, since nothing closes a pie there, press-drag-release, Esc and right-click.
A click on a tool or operator slot does nothing.

Sandro decided on 11 Nov 2026 that the pie Kompass draws holds 12 slots (#8).
Blender's own pie menu holds 8, so a pie of 12 gets no shortcut and a slot that leads to one is disabled there until Kompass draws the live pie (#22).
The canvas shows a pie of 12 as the table above gives it.
The editor cannot make a pie of 12 yet: it comes from a pie file.

## Editor host

Checked with a throwaway prototype in Blender 5.2.4 on 11 Nov 2026 (issue #17), with simulated input on Linux.
The prototype is not in the repository.

It hosted the editor in a `NodeTree` subclass named Kompass, with the slots as gizmos and the dial drawn behind them.

| Question | Answer |
|---|---|
| Does a node tree type become an editor? | Yes. `area.ui_type = "<tree idname>"` switches an area to it, and it is listed in the editor-type menu with its label and icon. |
| What does the empty editor show? | A dot grid, the header with View, Select, Add and Node menus and the tree selector, and a sidebar. |
| Does it need a node tree data-block? | Yes. Without one assigned to the editor, gizmo groups are not polled or drawn. The data-block is saved in the user's `.blend`. |
| Can the header be hidden? | Yes, with `space.show_region_header = False`, per area. Blender leaves a small arrow to bring it back. |
| Can the grid be hidden? | Yes. A `BACKDROP` draw handler that fills the region covers it. |
| Which sidebar tabs appear? | Blender's Group, Tool and View tabs beside the Kompass tab. A panel `poll` on `space_data.tree_type` keeps Kompass panels out of other node editors, but Blender's tabs cannot be removed. |
| Do gizmos work in the Node Editor? | Yes. A `GizmoGroup` with `bl_space_type = "NODE_EDITOR"` and `bl_region_type = "WINDOW"` draws, highlights under the pointer and runs its operator on a click. |
| Are gizmo positions in pixels? | Yes, region pixels. They stay in place and clickable when the node view below is zoomed or panned. |
| Does scroll and drag still move the node view? | Yes. The wheel zooms and middle-drag pans it under the canvas. With the grid covered nothing visible moves. |
| Do node shortcuts still work? | Yes. Shift+A opens the node Add menu, which is empty apart from Search. |
| Can `GIZMO_GT_button_2d` be a slot? | It can be placed and sized freely and shows a Blender icon, but it is a circle with no label. |
| Can a slot be drawn by Kompass? | Yes. A `Gizmo` subclass with `draw` and `test_select` draws a square slot with a `blf` label, highlights on hover and runs its target operator on a click. |
| Does a gizmo need an operator for a click? | No. Without a target operator it gets `invoke` on press and `exit` on release. With one, Blender shows the operator's tooltip over the canvas. |
| Which sidebar tab is open first? | Blender's Group tab, not Kompass. |
| Does the sidebar take space from the canvas? | No, it lies over it. The canvas subtracts its width to centre the pie. |
| What draws above what? | `BACKDROP`, then gizmos, then `POST_PIXEL`. The dial belongs in `BACKDROP`. |
| Does a draw handler fire in other node editors? | It is registered for the space type, so it returns early unless `space_data.tree_type` is Kompass. |
| Is a modal operator needed? | Only while a tool is carried. A modal started from the canvas receives pointer moves and ends on the next click, and that click does not also reach the gizmo under it. |
| Press on a sidebar button, drag, release on the canvas? | Does not work: the button does nothing. Click, move, click stays. |
| What does `wm.window_new()` give? | A window of 1216 by 720 px from a 1280 by 800 px parent, showing a copy of the area it was called from. |
| Is the Kompass window saved in the `.blend`? | Yes. Save and reopen brings the window back with the Kompass editor and its tree. A new file has neither. |

Sandro chose this host on 11 Nov 2026.

Not checked: a `.blend` saved with the Kompass window, opened without Kompass installed; trackpad gestures; a real mouse; macOS and Windows.

## Open questions

- Whether 12 slots can be hit blind with a flick: east and west are selected within 22°, their neighbours within 24°, against Blender's 45° (#22).
- Signal red for the selected slot differs from Blender, where selection follows the user's theme.
  Sandro chose red on 10 Nov 2026.
- The native pie cannot open sub-pies on hover: Blender's pie handler has no hover timer.
  In the native pie a sub-pie opens when its slot is chosen, centred on the pointer, and then waits for a click.
  Checked in Blender 5.2.4 on 11 Nov 2026.
