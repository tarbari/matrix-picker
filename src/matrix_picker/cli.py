import argparse
from pathlib import Path

from .export import render_markdown
from .models import TEAM_SIZE, Session
from .roster import RosterSource, TomlRosterSource, load_teams, save_teams


def describe(session: Session, name: str, ignore_team: int | None = None) -> str:
    c = session.roster[name]
    tags = ", ".join(c.roles + c.buffs)
    left = session.remaining(name, ignore_team)
    return f"{name} [{left}/{c.max_uses} uses]" + (f" - {tags}" if tags else "")


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return "q"


def yes(prompt: str) -> bool:
    return ask(f"{prompt} [y/N] ").lower() in ("y", "yes")


def pick_team(session: Session, ignore_team: int | None = None) -> list[str] | None:
    """Prompt for TEAM_SIZE characters; returns None if cancelled."""
    chosen: list[str] = []
    while len(chosen) < TEAM_SIZE:
        options = [
            c.name for c in session.available(ignore_team) if c.name not in chosen
        ]
        if not options:
            print("Not enough characters available.")
            return None
        print(f"\nPick character {len(chosen) + 1}/{TEAM_SIZE} (empty to cancel):")
        for i, name in enumerate(options, 1):
            print(f"  {i}. {describe(session, name, ignore_team)}")
        answer = ask("> ")
        if not answer:
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            chosen.append(options[int(answer) - 1])
        elif answer in options:
            chosen.append(answer)
        else:
            print("Invalid choice.")
    return chosen


def build_teams(session: Session, state_path: Path) -> None:
    while session.can_form_team():
        team = pick_team(session)
        if team is None:
            return
        session.teams.append(team)
        save_teams(state_path, session.teams)
        print(f"Team {len(session.teams)}: {', '.join(team)}")
        if not session.can_form_team():
            break
        if not yes("Form another team?"):
            return
    print(f"Fewer than {TEAM_SIZE} characters have uses left.")


def show_summary(session: Session) -> None:
    print()
    if not session.teams:
        print("No teams picked.")
    for i, team in enumerate(session.teams, 1):
        print(f"Team {i}: {', '.join(team)}")
    print("\nRoster:")
    for name in session.roster:
        print(f"  {describe(session, name)}")


def choose_team_index(session: Session, action: str) -> int | None:
    if not session.teams:
        print("No teams picked.")
        return None
    for i, team in enumerate(session.teams, 1):
        print(f"  {i}. {', '.join(team)}")
    answer = ask(f"Team to {action} (empty to cancel): ")
    if answer.isdigit() and 1 <= int(answer) <= len(session.teams):
        return int(answer) - 1
    return None


def edit_team(session: Session, state_path: Path) -> None:
    index = choose_team_index(session, "edit")
    if index is None:
        return
    team = pick_team(session, ignore_team=index)
    if team is not None:
        session.teams[index] = team
        save_teams(state_path, session.teams)


def remove_team(session: Session, state_path: Path) -> None:
    index = choose_team_index(session, "remove")
    if index is not None:
        session.teams.pop(index)
        save_teams(state_path, session.teams)


MENU = """
Endstate Matrix picker
  1. Pick teams
  2. Summary
  3. Edit a team
  4. Remove a team
  5. Reset (new set of teams)
  6. Export to Markdown
  q. Quit"""


def run(source: RosterSource, state_path: Path, export_path: Path) -> None:
    roster = source.load()
    session = Session(roster, load_teams(state_path, roster))
    overused = [n for n in roster if session.remaining(n) < 0]
    if overused:
        print(f"Warning: over max uses (roster changed?): {', '.join(overused)}")
    while True:
        print(MENU)
        choice = ask("> ").lower()
        if choice == "1":
            build_teams(session, state_path)
        elif choice == "2":
            show_summary(session)
        elif choice == "3":
            edit_team(session, state_path)
        elif choice == "4":
            remove_team(session, state_path)
        elif choice == "5":
            if yes("Discard all teams and restore all uses?"):
                session.teams.clear()
                save_teams(state_path, session.teams)
        elif choice == "6":
            export_path.write_text(render_markdown(session))
            print(f"Exported to {export_path}")
        elif choice in ("q", "quit"):
            return
        else:
            print("Unknown option.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Endstate Matrix team picker")
    parser.add_argument("--roster", type=Path, default=Path("roster.toml"))
    parser.add_argument("--state", type=Path, default=Path("state.json"))
    parser.add_argument("--export", type=Path, default=Path("teams.md"))
    args = parser.parse_args()
    if not args.roster.exists():
        parser.error(f"Roster file not found: {args.roster} (see roster.example.toml)")
    run(TomlRosterSource(args.roster), args.state, args.export)
