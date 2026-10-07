# matrix-picker

Team builder (GUI and interactive CLI) for building teams for the Wuthering Waves Endstate Matrix event.

```
cp roster.example.toml roster.toml   # edit with your characters
uv run matrix-picker [--roster F] [--state F] [--export F]
```

The roster (read-only) defines characters with `name`, `max_uses` (default 1), `roles`, `tags` and an optional `image`. Picked teams are stored in `state.json`; remaining uses are derived from them. Reset starts a new set of teams.

## GUI

```
uv run matrix-picker-gui [--roster F] [--state F] [--export F]
```

Built with Qt (PySide6), so it runs on Windows, Linux and macOS. Click a character on the left (or drag it onto a team) to add it to the next free slot; click a filled slot to remove it. There is always one empty team at the bottom. State is shared with the CLI.

### Character images

Add an optional `image` to a roster entry (path relative to the roster file); it is shown left of the name in the character list and in the team slots:

```toml
[[characters]]
name = "Iuno"
image = "images/iuno.png"
```

Recommended: square, 64x64 px (128x128 px for high-DPI screens); icons are displayed at 32x32 logical px. Supported formats: PNG (recommended, supports transparency), JPEG, BMP, GIF, and WebP. Missing files are ignored.

The GUI has "Show roles" and "Show tags" checkboxes that hide either kind of tag in the character list. Each team is shown as one row.

## Building a single executable

PyInstaller bundles the GUI into one file (Python and Qt included, ~60 MB). It cannot cross-compile, so build on each target OS:

```
uv sync
uv run pyinstaller matrix-picker.spec   # -> dist/matrix-picker (matrix-picker.exe on Windows)
```

The executable takes the same `--roster/--state/--export` options; paths default to the current directory, so keep `roster.toml` next to where you run it. Pushing a `v*` tag runs `.github/workflows/release.yml`, which builds for Windows, Linux and macOS and attaches zips to a GitHub release. macOS/Windows builds are unsigned, so expect Gatekeeper/SmartScreen warnings.
