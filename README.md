# matrix-picker

> [!IMPORTANT]
> This project is completely written by AI. I have read through the code and it seems fine, and the app works on my computer. I hope it works on yours as well.

A team builder for the Wuthering Waves **Endstate Matrix** event. Pick teams of three from your roster while tracking how many times each character can still be used. It comes with a cross-platform desktop GUI (Qt / PySide6) and an interactive CLI.

## Features

- Click a character, or drag and drop it, to put it in the next free team slot
- Per-character use limits (`max_uses`), tracked automatically
- Optional character images, role tags and other tags
- Teams are saved to `state.json` between runs
- Export the teams to Markdown
- Runs on Windows, Linux and macOS

## Requirements

- [uv](https://docs.astral.sh/uv/) and Python 3.12+ (uv installs Python for you), **or**
- the prebuilt single executable from the [Releases](https://github.com/tarbari/matrix-picker/releases) page (no Python needed)

## Running with uv

```
git clone https://github.com/tarbari/matrix-picker.git
cd matrix-picker
uv run matrix-picker-gui    # GUI
uv run matrix-picker        # interactive CLI
```

Both accept `--roster FILE` (default `roster.toml`), `--state FILE` (default `state.json`) and `--export FILE` (default `teams.md`). Paths are relative to the current directory.

If the roster file doesn't exist, a template is created with a single example character. Edit it to add your own.

## Running the single executable

1. Download the zip for your OS from the [Releases](https://github.com/tarbari/matrix-picker/releases) page and extract it.
2. Put the executable in its own folder; `roster.toml` and `state.json` are created next to where you run it.
3. Run `matrix-picker` (`matrix-picker.exe` on Windows). It accepts the same options as above.

The builds are unsigned, so Windows SmartScreen or macOS Gatekeeper may warn on first launch. On macOS and Linux you may need `chmod +x matrix-picker`.

## Using the GUI

- Characters are on the left; teams are on the right, one row per team of three.
- Click a character to add it to the first team with a free slot, or drag it onto a specific team.
- Click a filled slot to remove its character.
- Pressing Enter in the search box adds the first matching character that still has uses left.
- The search box filters the character list by name. Start with `tag:` or `role:` to search tags or roles instead (e.g. `tag:shield`, `role:sub`). Matching is case-insensitive and partial.
- There is always one empty team at the bottom.
- "Show roles" and "Show tags" hide those labels in the character list.
- "Export to Markdown" writes the teams; "Reset" discards all teams and restores all uses.

## Roster file format

The roster is a [TOML](https://toml.io) file with one `[[characters]]` table per character:

```toml
[[characters]]
name = "Iuno"
max_uses = 2
roles = ["Sub DPS"]
tags = ["HA Amp", "Lib DMG", "Shield"]
image = "images/iuno.png"
```

| Key        | Required | Default | Description                                                       |
|------------|----------|---------|-------------------------------------------------------------------|
| `name`     | yes      |         | Unique character name                                             |
| `max_uses` | no       | `1`     | How many teams the character may appear in                        |
| `roles`    | no       | `[]`    | Free-form role labels, e.g. `"Main DPS"`, `"Support"`             |
| `tags`     | no       | `[]`    | Free-form labels, e.g. buffs                                      |
| `image`    | no       |         | Image path, relative to the roster file; missing files are ignored |

Images are shown left of the name in the list and team slots. Use square images, 64x64 px (128x128 px for high-DPI screens); they display at 32x32 logical px. Supported formats: PNG (recommended), JPEG, BMP, GIF and WebP.

See `roster.example.toml` for a larger example. The roster is never modified by the app; picked teams go in `state.json`, and remaining uses are derived from them.

## Building the executable

PyInstaller can't cross-compile, so build on each target OS:

```
uv sync
uv run pyinstaller matrix-picker.spec   # -> dist/matrix-picker
```

Pushing a `v*` tag runs `.github/workflows/release.yml`, which builds for Windows, Linux and macOS and attaches zips to a GitHub release.

## Project layout

```
src/matrix_picker/
  models.py   characters, teams and use-tracking logic
  roster.py   roster loading, template creation, state persistence
  export.py   Markdown export
  cli.py      interactive CLI
  gui.py      Qt GUI
```
