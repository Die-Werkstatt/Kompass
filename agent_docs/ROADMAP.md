# Kompass: roadmap

Intent, not record. What is done lives in the code and the closed issues; this
file says what is next and why. Unchecked items are not done.

Each item is one pull request. An item depends on the ones above it in its own
list unless it says otherwise.

## Now

Milestone 0, foundations (#4).

- [ ] Extension scaffold, licence file, unit test and build checks (#11)
- [ ] Pie data model, validation and JSON format in a `core` package that never
      imports `bpy` (#12)
- [ ] Pie file in the extension user directory, with atomic writes and a kept
      copy of a corrupt file; headless smoke test script (#13, #21)

Still to decide in #10: the canvas font and the icon licence. Until then the
plan assumes Blender's own UI font and CC0 icons.

## Next

Milestone 1, pies open from shortcuts (#5).

- [ ] Open a stored pie as a native pie, with operator, tool, sub-pie and empty
      slots (#14, #15)
- [ ] Shortcut and context per pie, with the conflict warning (#16)
- [ ] Export and import in the add-on preferences, with a list of the stored
      pies (#20, first half). Uninstalling deletes the pie file, so this ships
      with the first version that can store a pie.

In parallel, from the moment the data model is merged:

- [ ] Editor spike: node-tree host, gizmo slots, short-lived modal (#17). It
      blocks all of Milestone 2 and needs Sandro's hands in Blender.

## Later

- [ ] Milestone 2, editor: canvas (#18), then pie list, search and
      pick-and-place (#19), then starter pies (#20, second half)
- [ ] Milestone 3, release Lite (#7)
- [ ] Milestone 4, Kompass-drawn pie, only if its spike says so (#8, #22)
