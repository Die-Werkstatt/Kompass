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

- [ ] Decide whether an edit of a pie's shortcut in Blender's Keymap
      preferences is read back (#16)

## Later

- [ ] Milestone 2, editor. The canvas shows a pie (#18) and the sidebar
      adds, renames, duplicates and deletes pies and sets their slot count,
      shortcut and context; a slot's menu fills, labels and clears it and sets its
      icon and its operator's settings, and a drag swaps two (#19).
      Left in #18: needle easing, the closing motion, the canvas font (#10),
      tool icons. Starter pies (#20) are `kompass/starter.json`, added from
      the preferences: Modeling, Object, Merge, Snap, Modifiers.
- [ ] Milestone 3, release Native, the edition that opens Blender's own pie
      menu (#7)
- [ ] Website download: a release `.zip` link that installs when dragged into
      Blender, plus an `index.json` from `extension server-generate` for
      updates. No installer app. On disk: `build.py` makes Kompass and
      Kompass Native, the site workflow attaches both to a release and the
      site links each button to its edition. Left: the first release, then a
      listing on extensions.blender.org.
- [ ] Milestone 4, the Kompass edition: a pie drawn by Kompass with 12 slots
      (#8, #22). On disk: a shortcut opens the drawn pie for a pie of 12, and
      for a pie of 8 with Kompass Pie on in the preferences. A line from the
      dial to the pointer shows the slot a click or release picks. Left:
      blind-hit testing by hand (#22).
