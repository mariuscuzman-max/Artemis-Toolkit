import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel

from scripts.python.artemis_control import is_artemis_running, get_artemis_activity

class ArtemisPill(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Artemis")
        self.setFixedSize(50, 100)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(40, 90)

        layout.addWidget(self.status_dot)
        self.setLayout(layout)

        self.move_to_right_center()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

        self.update_status()

    def move_to_right_center(self):
        screen = QApplication.primaryScreen().availableGeometry()

        x = screen.width() - self.width() - 10
        y = screen.height() - self.height() - 10

        self.move(x, y)

    def update_status(self):
        running = is_artemis_running()
        activity = get_artemis_activity()

        if not running:
            color = "rgba(178, 59, 59, 120)"  # roșu semi-transparent
        elif activity.get("state") == "active":
            color = "#3bb24a"  # verde doar când lucrează
        elif activity.get("state") == "error":
            color = "#d9a441"  # galben/portocaliu pentru eroare
        else:
            color = "rgba(120, 120, 120, 90)"  # idle transparent/gri

        self.status_dot.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 20px;
        }}
    """)


def main():
    print("Artemis pill is running...")
    

    app = QApplication(sys.argv)
    pill = ArtemisPill()
    pill.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()