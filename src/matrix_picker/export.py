from .models import Session


def render_markdown(session: Session) -> str:
    lines = ["# Endstate Matrix teams", ""]
    if not session.teams:
        lines += ["_No teams picked._", ""]
    for i, team in enumerate(session.teams, 1):
        lines.append(f"## Team {i}")
        for name in team:
            c = session.roster[name]
            tags = ", ".join(c.roles + c.tags)
            lines.append(f"- {name}" + (f" ({tags})" if tags else ""))
        lines.append("")
    lines += ["## Remaining uses", ""]
    for c in session.roster.values():
        lines.append(f"- {c.name}: {session.remaining(c.name)}/{c.max_uses}")
    return "\n".join(lines) + "\n"
