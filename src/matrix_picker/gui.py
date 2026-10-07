import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QMimeData, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
from .models import TEAM_SIZE, Character, Session, matches
from .roster import TomlRosterSource, ensure_roster, load_teams, save_teams

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


ICON_SIZE = QSize(32, 32)


def character_icon(c: Character) -> QIcon:
    if c.image and c.image.exists():
        return QIcon(str(c.image))
    return QIcon()


class Slot(QPushButton):
    """A team slot; click a filled one to remove its character."""

    def __init__(self, text: str, icon: QIcon | None = None) -> None:
        super().__init__(text)
        if icon:
            self.setIcon(icon)
        self.setIconSize(ICON_SIZE)
        self.setMinimumHeight(44)
        self.setEnabled(bool(text))
        self.setFlat(not text)


class TeamWidget(QFrame):
    def __init__(self, window: "MainWindow", index: int) -> None:
        super().__init__()
        self.window_ = window
        self.index = index
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(self)
        label = QLabel(f"<b>Team {index + 1}</b>")
        label.setMinimumWidth(60)
        layout.addWidget(label)
        team = window.session.teams[index]
        for slot in range(TEAM_SIZE):
            if slot < len(team):
                c = window.session.roster[team[slot]]
                button = Slot(c.name, character_icon(c))
                button.setToolTip("Click to remove")
                button.clicked.connect(
                    lambda _=False, s=slot: window.remove(self.index, s)
                )
            else:
                button = Slot("")
                button.setText("(empty)")
            layout.addWidget(button, 1)
        done = QCheckBox()
        done.setChecked(self.index in window.ticked)
        done.toggled.connect(
            lambda on: window.ticked.add(self.index)
            if on
            else window.ticked.discard(self.index)
        )
        layout.addWidget(done)

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
        self.ticked: set[int] = set()
        self.state_path = state_path
        self.export_path = export_path
        self.setWindowTitle("Endstate Matrix picker")
        self.resize(900, 600)

        self.list = CharacterList()
        self.list.setIconSize(ICON_SIZE)
        self.list.itemClicked.connect(self.on_item_clicked)
        left = QVBoxLayout()
        self.show_roles = QCheckBox("Show roles")
        self.show_roles.setChecked(True)
        self.show_tags = QCheckBox("Show tags")
        self.show_tags.setChecked(True)
        self.show_roles.toggled.connect(self.refresh)
        self.show_tags.toggled.connect(self.refresh)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name, or tag:... / role:...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        self.search.returnPressed.connect(self.add_first_match)
        left.addWidget(QLabel("<b>Characters</b>"))
        left.addWidget(self.search)
        left.addWidget(self.show_roles)
        left.addWidget(self.show_tags)
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

    def on_item_clicked(self, item: QListWidgetItem) -> None:
        self.add(item.data(Qt.ItemDataRole.UserRole))
        self.search.setFocus()
        self.search.selectAll()

    def add_first_match(self) -> None:
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsEnabled:
                self.on_item_clicked(item)
                return

    def label(self, c: Character, counts: bool = True) -> str:
        tags = (c.roles if self.show_roles.isChecked() else ()) + (
            c.tags if self.show_tags.isChecked() else ()
        )
        text = c.name
        if counts:
            text += f" [{self.session.remaining(c.name)}/{c.max_uses}]"
        return text + (f" - {', '.join(tags)}" if tags else "")

    def refresh(self) -> None:
        self.list.clear()
        for c in self.session.roster.values():
            if not matches(c, self.search.text()):
                continue
            left = self.session.remaining(c.name)
            item = QListWidgetItem(character_icon(c), self.label(c))
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
    if ensure_roster(args.roster):
        print(f"Created template roster at {args.roster}; edit it to add your characters.")
    roster = TomlRosterSource(args.roster).load()
    session = Session(roster, load_teams(args.state, roster))
    app = QApplication(sys.argv[:1])
    window = MainWindow(session, args.state, args.export)
    window.show()
    sys.exit(app.exec())
