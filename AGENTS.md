# AGENTS.md

Guide for AI agents working on matrix-picker: a team builder for the Wuthering Waves Endstate Matrix event, with a Qt GUI and an interactive CLI.

## Setup and running

- Python 3.12+, managed with [uv](https://docs.astral.sh/uv/). The only runtime dependency is `pyside6-essentials`.
- `uv sync` installs everything; `uv run matrix-picker-gui` starts the GUI, `uv run matrix-picker` the CLI.
- Both take `--roster`, `--state`, `--export`. A template `roster.toml` is created if missing; `roster.example.toml` is a larger sample.
- There is no test suite and no linter configured. Verify changes yourself (see below).

## Layout

```
src/matrix_picker/
  models.py   Character, Session (teams, done flags, use counting, add/remove, search matching)
  roster.py   TOML roster loading, template creation, state.json load/save
  export.py   Markdown export
  cli.py      interactive CLI
  gui.py      PySide6 GUI
packaging/gui_entry.py + matrix-picker.spec   PyInstaller build
.github/workflows/release.yml                 builds and publishes releases on v* tags
```

## Architecture rules

- Keep logic in `models.py` / `roster.py` and keep it UI-free; `gui.py` and `cli.py` only present and call it. Both front ends share one `state.json`, so changes to the state format must work in both.
- Remaining uses are derived from `Session.teams` and the roster's `max_uses`; never store them.
- `state.json` is `{"teams": [[names...]], "done": [bool...]}`. `done` is optional when loading (older files). The GUI keeps a trailing empty team in memory but never saves empty teams. Keep loading backward compatible.
- The roster is read-only; the app never modifies it. Image paths are resolved relative to the roster file.
- Roster keys are `name`, `max_uses`, `roles`, `tags`, `image`. (`buffs` was renamed to `tags`.)
- Must work on Windows, Linux and macOS: use `pathlib`, no platform-specific code, UTF-8 for files.

## Verifying changes

- Import check: `QT_QPA_PLATFORM=offscreen uv run python -c "import matrix_picker.gui"`.
- For GUI behaviour, write a throwaway script that sets `QT_QPA_PLATFORM=offscreen`, builds `MainWindow(Session(...), state_path, export_path)`, calls its methods and inspects `session.teams`/widgets. Delete it afterwards, and use temp paths for state/export files.
- Real mouse drag and drop can't be tested headless. On WSLg/Linux the system drag pixmap doesn't render; Windows is fine, so don't "fix" that.
- CLI: `echo q | uv run matrix-picker --roster /tmp/r.toml --state /tmp/s.json`.

## Docs

Update `README.md` whenever user-visible behaviour, the roster format or the state format changes. Keep this file in sync when the architecture or workflow changes.

## Releases and git

- Version lives in `pyproject.toml` (`version`); keep `uv.lock` in step (`uv lock`). Use semver: new features bump the minor, fixes the patch.
- Pushing a tag `vX.Y.Z` runs the release workflow, which builds with PyInstaller on all three OSes and attaches zips (including `LICENSE`) to a GitHub release. Only tag when asked, and bump the version first.
- Local build: `uv run pyinstaller matrix-picker.spec` -> `dist/` (git-ignored).
- Commit and push to `main` only when the user asks. End commit messages with `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.
- Privacy: don't put personal emails, names or local paths in files. Commit author metadata is public once the repo is, so check `git config user.email` is the GitHub noreply address.
- Never commit `roster.toml`, `state.json`, `teams.md` (git-ignored user data).
