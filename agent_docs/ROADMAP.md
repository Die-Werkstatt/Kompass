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

- [ ] Milestone 2, editor: canvas (#18), then pie list, search and
      pick-and-place (#19), then starter pies (#20, second half). Host and
      input as the spike found workable (`docs/design/README.md`, Editor
      host): a Kompass node tree type, slots as Kompass-drawn gizmos, the
      dial in a backdrop draw handler, a modal operator only while a tool is
      carried. Sandro has not confirmed this choice.
- [ ] Milestone 3, release Lite (#7)
- [ ] Milestone 4, Kompass-drawn pie, only if its spike says so (#8, #22)
