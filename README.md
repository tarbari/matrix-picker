# matrix-picker

Interactive CLI for building teams for the Wuthering Waves Endstate Matrix event.

```
cp roster.example.toml roster.toml   # edit with your characters
uv run matrix-picker [--roster F] [--state F] [--export F]
```

The roster (read-only) defines characters, role tags, buff tags and `max_uses`. Picked teams are stored in `state.json`; remaining uses are derived from them. Reset starts a new set of teams.
