# Kompass interface design

How the pie looks and behaves on the Kompass editor canvas.
[`pie-playground.html`](pie-playground.html) is a working mock-up: open it in a browser.
Variant **G · Bearing needle** is the chosen design; D, E and F stay in the file for comparison.

Blender draws the live pie menu itself, in the user's theme.
Everything below applies to the editor canvas, which Kompass draws with `gpu` and `blf`.

## Look

| Part | Value |
|---|---|
| Slot labels | Barlow SemiBold, capitals, tracking 0.08 em |
| Slots | square corners; ground `#0E0E0E`, outline `#2C2C2C` |
| Sub-pie marker | signal-red triangle in a slot's top-right corner |
| Centre dial | ring with a tick every 5°, longer every 45°, and the split compass needle |
| Outer arrow | signal-red triangle outside the ring; turns with the needle |
| Sub-pie dial | 72% of the main dial |
| Sub-pie title | pie name in capitals above the dial |
| Dial label | BACK in a sub-pie, CLOSE at the root, below the dial |
| Colours | see [`../brand/README.md`](../brand/README.md) |

## Behaviour

| Event | Result |
|---|---|
| Pointer moves | needle and outer arrow follow it; easing time constant 45 ms, shortest arc |
| Pointer within 8 px of the centre | needle holds its last heading |
| Pointer outside the dial ring | the nearest slot is selected |
| Pointer inside the dial ring | no slot is selected |
| Highlight | signal red, strength rises with distance past the ring and closeness to the needle; the selected slot keeps at least 30% |
| Pointer rests on a sub-pie slot for 100 ms | the sub-pie opens, centred on the pointer |
| Click on a tool slot | runs the tool and closes the pie |
| Press, drag over 250 ms, release on a slot | same as a click |
| Click on the dial, Esc or right-click | back one level; closes the pie at the root |
| Return from a sub-pie | the slot that opened it does not reopen until the pointer leaves it |
| Opening a sub-pie | the needle keeps its heading; it does not reset to north |

## Open questions

- Signal red for the selected slot differs from Blender, where selection follows the user's theme.
  Sandro chose red on 10 Nov 2026.
- Whether the native pie can open sub-pies on hover is not yet checked against Blender's source.
