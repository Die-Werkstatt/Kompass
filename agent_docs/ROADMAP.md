# Kompass: roadmap

Intent, not record. What is done lives in the code and the closed issues; this
file says what is next and why. Unchecked items are not done.

Each item is one pull request. An item depends on the ones above it in its own
list unless it says otherwise.

## Now

Milestone 0, foundations (#4).

- [ ] Manual test checklist in `docs/` for what only a person can judge (#21)

Still to decide in #10: the canvas font and the icon licence. Until then the
plan assumes Blender's own UI font and CC0 icons.

## Next

Milestone 1, pies open from shortcuts (#5).

- [ ] Warn when a pie's shortcut is already used in its keymap (#16). It needs
      somewhere to set a shortcut, so it comes with import or the editor.
- [ ] Export and import in the add-on preferences, with a list of the stored
      pies (#20, first half). Uninstalling deletes the pie file, so this ships
      with the first version that can store a pie, together with the user
      documentation that says so. Import is also the first caller of
      `core.store.save`.

In parallel:

- [ ] Editor spike: node-tree host, gizmo slots, short-lived modal (#17). It
      blocks all of Milestone 2 and needs Sandro's hands in Blender.

## Later

- [ ] Milestone 2, editor: canvas (#18), then pie list, search and
      pick-and-place (#19), then starter pies (#20, second half)
- [ ] Milestone 3, release Lite (#7)
- [ ] Milestone 4, Kompass-drawn pie, only if its spike says so (#8, #22)
