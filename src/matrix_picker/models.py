from dataclasses import dataclass, field
from pathlib import Path

TEAM_SIZE = 3


@dataclass(frozen=True)
class Character:
    name: str
    max_uses: int
    roles: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    image: Path | None = None


def matches(c: Character, query: str) -> bool:
    """Case-insensitive substring match: name by default, `tag:`/`role:` prefixes."""
    query = query.strip().lower()
    for prefix, values in (("tag:", c.tags), ("role:", c.roles)):
        if query.startswith(prefix):
            term = query[len(prefix) :].strip()
            return not term or any(term in v.lower() for v in values)
    return query in c.name.lower()


@dataclass
class Session:
    """Roster plus the teams picked so far; remaining uses are derived from the teams."""

    roster: dict[str, Character]
    teams: list[list[str]] = field(default_factory=list)
    done: list[bool] = field(default_factory=list)

    def _sync_done(self) -> None:
        del self.done[len(self.teams) :]
        self.done.extend([False] * (len(self.teams) - len(self.done)))

    def is_done(self, team_index: int) -> bool:
        self._sync_done()
        return self.done[team_index]

    def set_done(self, team_index: int, value: bool) -> None:
        self._sync_done()
        self.done[team_index] = value

    def add_team(self, team: list[str]) -> None:
        self._sync_done()
        self.teams.append(team)
        self.done.append(False)

    def remove_team(self, team_index: int) -> None:
        self._sync_done()
        del self.teams[team_index]
        del self.done[team_index]

    def clear(self) -> None:
        self.teams.clear()
        self.done.clear()

    def used(self, name: str, ignore_team: int | None = None) -> int:
        return sum(
            team.count(name)
            for i, team in enumerate(self.teams)
            if i != ignore_team
        )

    def remaining(self, name: str, ignore_team: int | None = None) -> int:
        return self.roster[name].max_uses - self.used(name, ignore_team)

    def available(self, ignore_team: int | None = None) -> list[Character]:
        return [
            c for c in self.roster.values() if self.remaining(c.name, ignore_team) > 0
        ]

    def can_form_team(self, ignore_team: int | None = None) -> bool:
        return len(self.available(ignore_team)) >= TEAM_SIZE

    def normalize(self) -> None:
        """Drop empty teams and keep exactly one empty team at the end."""
        self._sync_done()
        kept = [(t, d) for t, d in zip(self.teams, self.done) if t]
        self.teams[:] = [t for t, _ in kept]
        self.done[:] = [d for _, d in kept]
        self.teams.append([])
        self.done.append(False)

    def can_add(self, name: str, team_index: int) -> bool:
        team = self.teams[team_index]
        return (
            len(team) < TEAM_SIZE
            and name not in team
            and self.remaining(name) > 0
        )

    def add(self, name: str, team_index: int | None = None) -> bool:
        """Add to the given team, or the first team that accepts it."""
        candidates = range(len(self.teams)) if team_index is None else [team_index]
        for i in candidates:
            if self.can_add(name, i):
                self.teams[i].append(name)
                self.normalize()
                return True
        return False

    def remove(self, team_index: int, slot: int) -> None:
        del self.teams[team_index][slot]
        self.normalize()
