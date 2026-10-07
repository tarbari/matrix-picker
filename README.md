# matrix-picker

Interactive CLI for building teams for the Wuthering Waves Endstate Matrix event.

```
cp roster.example.toml roster.toml   # edit with your characters
uv run matrix-picker [--roster F] [--state F] [--export F]
```

The roster (read-only) defines characters, role tags, buff tags and `max_uses`. Picked teams are stored in `state.json`; remaining uses are derived from them. Reset starts a new set of teams.

## GUI

```
uv run matrix-picker-gui [--roster F] [--state F] [--export F]
```

Built with Qt (PySide6), so it runs on Windows, Linux and macOS. Click a character on the left (or drag it onto a team) to add it to the next free slot; click a filled slot to remove it. There is always one empty team at the bottom. State is shared with the CLI.
