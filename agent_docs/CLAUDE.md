# Kompass

Kompass is a Blender extension (GPL-3.0-or-later) for artists who want their
own pie menus. A pie of 4 or 8 slots opens as Blender's pie menu on its shortcut, or
as the pie Kompass draws, as a pie of 12 always does. Slots are filled in the editor.

## Stack
- Blender 5.2 LTS is the minimum version. It ships Python 3.13.
- Python standard library only inside the add-on. No bundled wheels.
- pytest for unit tests, ruff through aislop for lint.

## Project structure

- `kompass/`: the extension; everything in it ships in the `.zip`.
  - `core/`: the pie model, validation and JSON format (`model.py`), reading
    and writing a pie file on disk (`store.py`), choosing pies for export and
    merging imported ones (`transfer.py`), canvas geometry and motion
    (`layout.py`), changes to the pies (`edit.py`).
  - `blender/`: everything that needs `bpy`. `storage.py` holds the pies
    loaded from `pies.json`, `pie.py` opens one as a native pie menu,
    `keymaps.py` gives each its shortcut, `tools.py` reads the tool list,
    `files.py` exports and imports, `preferences.py` lists the pies, `editor.py`
    is the editor, `shortcuts.py`, `slots.py`, `canvas.py` its panel, menu and pie; `live.py` opens the drawn pie, `stage.py` moves it. `starter.json`: the starter pies.
- `tests/`: unit tests, run without Blender. `tests/data/example.json` is a
  pie file. `tests/smoke/` runs inside Blender: `checks.py` without a window,
  `interface.py` with one, pressing shortcuts through simulated events.
- `docs/`: brand notes (`brand/`), the pie design (`design/`), the release
  checklist (`manual-test.md`). `site/`: the website (`workflows/site.yml`).
- `agent_docs/`: these instructions, the roadmap and the dependency inventory.

## Architecture rules

- `kompass/core/` never imports `bpy`. A unit test enforces it.
- Only files in `kompass/blender/` import Blender's modules. Each carries the
  `aislop-ignore-file hallucinated-import` line: aislop cannot see modules
  that Blender provides.
- `import kompass` works without Blender: `kompass/__init__.py` imports
  `kompass.blender` inside `register()`, never at the top.
- Every pie file is read by `core.model.loads` and written by
  `core.store.save`. Both validate and refuse unknown keys and slot types.
- `kompass.blender.ADDON` is the add-on identifier. Never write the literal
  `bl_ext` or a repository name in add-on code.
- Write files only under `bpy.utils.extension_path_user`, never beside
  `__file__`. Blender keeps that directory across upgrades and deletes it,
  with `pies.json`, on uninstall.
- `wm.keyconfigs.addon` is `None` in background mode; check before use.
- `bl_ui` is not documented API: only `blender/tools.py` imports it.
- A slot whose tool or operator is missing draws disabled and never raises.
- Canvas lengths live in `core/layout.py`, in pixels at UI scale 1. Only
  `paint.py` turns them into a region's pixels.
- No `eval` or `exec`.
- Bundled images, icons and fonts must be CC0 (extensions.blender.org terms
  1.2). The files in `docs/brand/` stay out of `kompass/`.

## Build & dev commands

```sh
python3 .claude/suite-check.py   # every health check in .claude/suite.json
pytest -q                        # unit tests
python3 tests/smoke/run.py       # build, install and check in Blender
xvfb-run -a python3 tests/smoke/run.py --interface   # the same, with a window
blender --command extension build --source-dir kompass   # kompass-<version>.zip
```

Both Blender tests use a temporary profile and are skipped where `blender` or
`xvfb-run` is missing. CI (`.github/workflows/checks.yml`) runs both.

## Task tracking
Work is tracked in GitHub Issues. Every issue carries a `type:`, an `area:` and
exactly one priority (`p0`-`p3`) label. The issue forms ask for it and the
`issue-priority` workflow applies it; an issue opened through the API (by an
agent) sets the label in the same call, `p2` when unclear. Close issues from
the pull request with `Fixes #N`.

## Commits & pull requests

- One pull request per piece of work, never one per tweak. Its `## Changelog`
  section gives each change a line (`- feature: ...`, `- fix: ...`,
  `- chore: ...`). Split only for risk, an independent revert or a different
  release.
- Changelog lines and titles are public release-notes copy: imperative,
  sentence case, no trailing period, no em dashes.
- Every pull request needs an `area:` label, plus a `type:` label when it has
  no Changelog section, before it can merge (the `pr-labelled` status). Which
  type: see `.github/pull_request_template.md`.

## Files that come from the template

This repo was created from sandrogekeler/AllesSandro and is kept in step with it
by Renovate (`.copier-answers.yml` records the version). Two kinds of file:

- **Locked** (re-applied on every template update): `.claude/suite-*.py`,
  `.github/workflows/{codeql,scorecard,pr-labelled,labels,template-guard,issue-priority}.yml`
  (CodeQL and Scorecard only on a public repo) and the optional `aislop.yml`,
  `claude.yml`, `.aislop/base.yml`, `.github/scripts/changelog-section.py`,
  `.github/scripts/release-notes.py`,
  `.claude/rules/{writing,simplicity,typography}.md`. Do not edit them here: change
  AllesSandro instead. A local edit is kept but shows up as a merge conflict on
  the next template update.
- **Seeded** (created once, owned by this repo): everything else, including
  this file.

A template-update PR with `<<<<<<< before updating` markers: see
`.claude/rules/template-files.md`.

## Docs

Describe what is on disk, in the present tense. Intent goes in
`agent_docs/ROADMAP.md` as an unchecked item. Unsure whether something landed?
Check before writing it down.

## Do not

- Commit secrets, `.env` files or credentials.
- Edit generated files or lockfiles by hand; regenerate them.

## Deeper rules, loaded on demand

`.claude/rules/*.md`: each one names the paths that load it.
