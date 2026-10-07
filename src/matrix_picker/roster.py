import json
import tomllib
from pathlib import Path
from typing import Protocol

from .models import Character


class RosterSource(Protocol):
    """Where owned characters come from; swap in an API-backed source later."""

    def load(self) -> dict[str, Character]: ...


TEMPLATE = """\
# Roster of owned characters. See the README for the format.
[[characters]]
name = "Iuno"
max_uses = 1
roles = ["Sub DPS"]
tags = ["HA Amp", "Lib DMG", "Shield"]
"""


def ensure_roster(path: Path) -> bool:
    """Write a template roster if missing; returns True if it was created."""
    if path.exists():
        return False
    path.write_text(TEMPLATE, encoding="utf-8")
    return True


class TomlRosterSource:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Character]:
        with self.path.open("rb") as f:
            data = tomllib.load(f)
        roster: dict[str, Character] = {}
        for entry in data.get("characters", []):
            name = entry["name"]
            if name in roster:
                raise ValueError(f"Duplicate character in roster: {name}")
            roster[name] = Character(
                name=name,
                max_uses=int(entry.get("max_uses", 1)),
                roles=tuple(entry.get("roles", [])),
                tags=tuple(entry.get("tags", [])),
                image=(
                    self.path.parent / entry["image"] if "image" in entry else None
                ),
            )
        return roster


def load_teams(path: Path, roster: dict[str, Character]) -> list[list[str]]:
    if not path.exists():
        return []
    teams = json.loads(path.read_text())["teams"]
    # Drop characters removed from the roster; over-used ones are caught by the menu.
    return [[n for n in team if n in roster] for team in teams]


def save_teams(path: Path, teams: list[list[str]]) -> None:
    path.write_text(json.dumps({"teams": teams}, indent=2) + "\n")
