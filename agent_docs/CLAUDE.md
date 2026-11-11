# Kompass

Kompass is a Blender add-on for artists who want their own pie menus: each pie
holds up to 8 tools, operators or sub-pies and opens on its own shortcut. It is
distributed as a Blender extension under GPL-3.0-or-later. The repo holds the
installable scaffold; no pie code exists yet (see `ROADMAP.md`).

## Stack
- Blender 5.2 LTS is the minimum version (`blender_version_min` in the
  manifest). It ships Python 3.13, so add-on code may use 3.13 syntax.
- Python standard library only inside the add-on. No bundled wheels.
- pytest for unit tests, ruff through aislop for lint.

## Project structure

- `kompass/`: the extension. `blender_manifest.toml` and the add-on package.
  Everything in here ships in the `.zip`.
- `tests/`: unit tests, run without Blender.
- `docs/brand/`, `docs/design/`: logo files, brand notes and the pie design
  with its playground. Not shipped in the extension.
- `agent_docs/`: these instructions, the roadmap and the dependency inventory.

## Architecture rules

- `import kompass` works without Blender. Modules that need `bpy` are imported
  inside `register()`, never at the top of `kompass/__init__.py`.
- Use `__package__` for the add-on identifier. Never write the literal `bl_ext`
  or a repository name in add-on code.
- Write files only under `bpy.utils.extension_path_user(__package__)`. Never
  build a write path from `__file__`: the extension directory is cleared on
  every upgrade.
- `wm.keyconfigs.addon` is `None` in background mode; check before use.
- No `eval` or `exec`.
- Bundled images, icons and fonts must be CC0 (extensions.blender.org terms
  1.2). The files in `docs/brand/` stay out of `kompass/`.

## Build & dev commands

```sh
python3 .claude/suite-check.py   # every health check in .claude/suite.json
pytest -q                        # unit tests
blender --command extension build --source-dir kompass   # kompass-<version>.zip
```

The build check is skipped where `blender` is not on `PATH`. CI
(`.github/workflows/checks.yml`) downloads Blender 5.2, builds the extension,
installs it and enables it.

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
