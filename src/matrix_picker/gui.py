import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .export import render_markdown
from .models import TEAM_SIZE, Session
from .roster import TomlRosterSource, load_teams, save_teams

MIME = "application/x-matrix-picker-character"


class CharacterList(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDropMode.DragOnly)

    def mimeData(self, items: list[QListWidgetItem]) -> QMimeData:
        data = QMimeData()
        data.setData(MIME, items[0].data(Qt.ItemDataRole.UserRole).encode())
        return data


class Slot(QPushButton):
    """A team slot; click a filled one to remove its character."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setMinimumHeight(36)
        self.setEnabled(bool(text))
        self.setFlat(not text)


class TeamWidget(QFrame):
    def __init__(self, window: "MainWindow", index: int) -> None:
        super().__init__()
        self.window_ = window
        self.index = index
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Team {index + 1}</b>"))
        team = window.session.teams[index]
        for slot in range(TEAM_SIZE):
            if slot < len(team):
                button = Slot(team[slot])
                button.setToolTip("Click to remove")
                button.clicked.connect(
                    lambda _=False, s=slot: window.remove(self.index, s)
                )
            else:
                button = Slot("")
                button.setText("(empty)")
            layout.addWidget(button)

    def _name(self, event) -> str | None:
        if event.mimeData().hasFormat(MIME):
            return bytes(event.mimeData().data(MIME)).decode()
        return None

    def dragEnterEvent(self, event) -> None:
        name = self._name(event)
        if name and self.window_.session.can_add(name, self.index):
            event.acceptProposedAction()

    dragMoveEvent = dragEnterEvent

    def dropEvent(self, event) -> None:
        name = self._name(event)
        if name:
            self.window_.add(name, self.index)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self, session: Session, state_path: Path, export_path: Path) -> None:
        super().__init__()
        self.session = session
        self.state_path = state_path
        self.export_path = export_path
        self.setWindowTitle("Endstate Matrix picker")
        self.resize(900, 600)

        self.list = CharacterList()
        self.list.itemClicked.connect(
            lambda item: self.add(item.data(Qt.ItemDataRole.UserRole))
        )
        left = QVBoxLayout()
        left.addWidget(QLabel("<b>Characters</b>"))
        left.addWidget(self.list)

        self.teams_layout = QVBoxLayout()
        self.teams_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        holder = QWidget()
        holder.setLayout(self.teams_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)

        export = QPushButton("Export to Markdown")
        export.clicked.connect(self.export)
        reset = QPushButton("Reset")
        reset.clicked.connect(self.reset)
        buttons = QHBoxLayout()
        buttons.addWidget(export)
        buttons.addWidget(reset)
        right = QVBoxLayout()
        right.addWidget(QLabel("<b>Teams</b>"))
        right.addWidget(scroll)
        right.addLayout(buttons)

        root = QHBoxLayout()
        root.addLayout(left, 1)
        root.addLayout(right, 2)
        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

        self.session.normalize()
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for c in self.session.roster.values():
            left = self.session.remaining(c.name)
            tags = ", ".join(c.roles + c.buffs)
            item = QListWidgetItem(
                f"{c.name} [{left}/{c.max_uses}]" + (f" - {tags}" if tags else "")
            )
            item.setData(Qt.ItemDataRole.UserRole, c.name)
            if left <= 0:
                item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list.addItem(item)
        while self.teams_layout.count():
            w = self.teams_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        for i in range(len(self.session.teams)):
            self.teams_layout.addWidget(TeamWidget(self, i))

    def save(self) -> None:
        save_teams(self.state_path, [t for t in self.session.teams if t])
        self.refresh()

    def add(self, name: str, team_index: int | None = None) -> None:
        if self.session.add(name, team_index):
            self.save()

    def remove(self, team_index: int, slot: int) -> None:
        self.session.remove(team_index, slot)
        self.save()

    def reset(self) -> None:
        answer = QMessageBox.question(
            self, "Reset", "Discard all teams and restore all uses?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.session.teams.clear()
            self.session.normalize()
            self.save()

    def export(self) -> None:
        teams = self.session.teams
        self.session.teams = [t for t in teams if t]
        try:
            self.export_path.write_text(render_markdown(self.session))
        finally:
            self.session.teams = teams
        QMessageBox.information(self, "Export", f"Exported to {self.export_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Endstate Matrix team picker (GUI)")
    parser.add_argument("--roster", type=Path, default=Path("roster.toml"))
    parser.add_argument("--state", type=Path, default=Path("state.json"))
    parser.add_argument("--export", type=Path, default=Path("teams.md"))
    args = parser.parse_args()
    if not args.roster.exists():
        parser.error(f"Roster file not found: {args.roster} (see roster.example.toml)")
    roster = TomlRosterSource(args.roster).load()
    session = Session(roster, load_teams(args.state, roster))
    app = QApplication(sys.argv[:1])
    window = MainWindow(session, args.state, args.export)
    window.show()
    sys.exit(app.exec())
