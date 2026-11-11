# Kompass: roadmap

Intent, not record. What is done lives in the code and the closed issues; this
file says what is next and why. Unchecked items are not done.

Each item is one pull request. An item depends on the ones above it in its own
list unless it says otherwise.

## Now

Milestone 0, foundations (#4).

- [ ] Run `docs/manual-test.md` by hand in Blender 5.2 for the first time
      (Sandro)

Still to decide in #10: the canvas font and the icon licence. Until then the
plan assumes Blender's own UI font and CC0 icons.

## Next

Milestone 1, pies open from shortcuts (#5).

- [ ] Search the keymaps that are active together, such as "Object Mode"
      beside "3D View", when warning that a shortcut is taken, and decide
      whether an edit in Blender's Keymap preferences is read back (#16)

## Later

- [ ] Milestone 2, editor. The canvas shows a pie (#18) and the sidebar
      adds, renames, duplicates and deletes pies and sets their shortcut and
      context; a slot's menu fills, labels and clears it and sets its
      operator's settings, and a drag swaps two (#19).
      Left in #18: needle easing, the closing motion, the canvas font (#10),
      tool icons. Left in #19, in this order: slot icon,
      choosing 8 or 12 slots for a pie, dragging into a sub-pie, preview of
      the real pie. Then starter pies (#20, second half).
- [ ] Milestone 3, release Native, the edition that opens Blender's own pie
      menu (#7)
- [ ] Milestone 4, the Kompass edition: a pie drawn by Kompass with 12 slots,
      only if its spike says so (#8, #22). Until then a pie of 12 slots shows
      in the editor and cannot be opened.
