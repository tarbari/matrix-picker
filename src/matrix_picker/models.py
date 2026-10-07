from dataclasses import dataclass, field

TEAM_SIZE = 3


@dataclass(frozen=True)
class Character:
    name: str
    max_uses: int
    roles: tuple[str, ...] = ()
    buffs: tuple[str, ...] = ()


@dataclass
class Session:
    """Roster plus the teams picked so far; remaining uses are derived from the teams."""

    roster: dict[str, Character]
    teams: list[list[str]] = field(default_factory=list)

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
