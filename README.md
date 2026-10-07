# matrix-picker

Interactive CLI for building teams for the Wuthering Waves Endstate Matrix event.

```
cp roster.example.toml roster.toml   # edit with your characters
uv run matrix-picker [--roster F] [--state F] [--export F]
```

The roster (read-only) defines characters, role tags, other tags, an optional `image` and `max_uses`. Picked teams are stored in `state.json`; remaining uses are derived from them. Reset starts a new set of teams.

## GUI

```
uv run matrix-picker-gui [--roster F] [--state F] [--export F]
```

Built with Qt (PySide6), so it runs on Windows, Linux and macOS. Click a character on the left (or drag it onto a team) to add it to the next free slot; click a filled slot to remove it. There is always one empty team at the bottom. State is shared with the CLI.

### Character images

Add an optional `image` to a roster entry (path relative to the roster file); it is shown left of the name in the character list and in the teams:

```toml
[[characters]]
name = "Iuno"
image = "images/iuno.png"
```

Recommended: square, 64x64 px (128x128 px for high-DPI screens); icons are displayed at 32x32 logical px. Supported formats: PNG (recommended, supports transparency), JPEG, BMP, GIF, and WebP. Missing files are ignored.

The GUI has "Show roles" and "Show tags" checkboxes to hide either kind of tag. Each team is shown as one row.
