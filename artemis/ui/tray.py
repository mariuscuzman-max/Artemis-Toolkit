import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from artemis.core.cleanup_tracker import (
    get_cleanup_candidates,
    get_cleanup_stats,
    postpone_cleanup_items,
    delete_cleanup_items, 
)
from scripts.python.artemis_control import get_artemis_activity, is_artemis_running


class ArtemisTray:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        icon_dir = ROOT_DIR / "icons"

        self.icon_idle = QIcon(str(icon_dir / "idle.png"))
        self.icon_active = QIcon(str(icon_dir / "active.png"))
        self.icon_warning = QIcon(str(icon_dir / "warning.png"))
        self.icon_error = QIcon(str(icon_dir / "error.png"))

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon_idle)
        self.tray.setToolTip("Artemis - Idle")
        self.tray.setVisible(True)

        menu = QMenu()
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.app.quit)
        self.tray.setContextMenu(menu)

        self.tray.activated.connect(self.on_tray_click)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

        self.update_status()

    def update_status(self):
        running = is_artemis_running()
        activity = get_artemis_activity()
        state = activity.get("state", "idle")

        cleanup_count, cleanup_size = get_cleanup_stats()
        cleanup_mb = round(cleanup_size / (1024 * 1024), 1)

        cleanup_candidates = get_cleanup_candidates()
        candidate_count = len(cleanup_candidates)

        cleanup_text = ""
        if cleanup_count > 0:
            cleanup_text = f" | Cleanup: {cleanup_count} items / {cleanup_mb} MB"

        print("Tray sees:", running, state, "| candidates:", candidate_count)

        if not running:
            self.tray.setIcon(self.icon_error)
            self.tray.setToolTip(f"Artemis - Not running{cleanup_text}")
            return

        if state == "error":
            self.tray.setIcon(self.icon_error)
            self.tray.setToolTip(f"Artemis - Error{cleanup_text}")
            return

        if state == "active":
            self.tray.setIcon(self.icon_active)
            self.tray.setToolTip(f"Artemis - Working{cleanup_text}")
            return

        if state == "waiting":
            self.tray.setIcon(self.icon_warning)
            self.tray.setToolTip(f"Artemis - Waiting for input{cleanup_text}")
            return

        if candidate_count > 0:
            self.tray.setIcon(self.icon_warning)
            self.tray.setToolTip(
                f"Artemis - Review needed: {candidate_count} items | "
                f"Cleanup total: {cleanup_count} items / {cleanup_mb} MB"
            )
            return

        self.tray.setIcon(self.icon_idle)
        self.tray.setToolTip(f"Artemis - Idle{cleanup_text}")

    def on_tray_click(self, reason):
        if reason not in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            return

        candidates = get_cleanup_candidates()
        
        if not candidates:
            return

        count = len(candidates)
        total_size = sum(item.get("size", 0) for item in candidates)
        mb = round(total_size / (1024 * 1024), 1)

        message = QMessageBox()
        message.setWindowTitle("Artemis Cleanup")
        message.setText(
            f"Artemis found {count} file(s) ready for cleanup.\n\n"
            f"Potential space to free: {mb} MB\n\n"
            f"What do you want to do?"
        )

        delete_button = message.addButton(
            "Delete files",
            QMessageBox.ButtonRole.AcceptRole,
        )
        ignore_button = message.addButton(
            "Ignore for now",
            QMessageBox.ButtonRole.RejectRole,
        )

        message.exec()

        if message.clickedButton() == delete_button:
            self.delete_cleanup_candidates(candidates)

        elif message.clickedButton() == ignore_button:
            postpone_cleanup_items([item.get("path", "") for item in candidates])
            print("Cleanup postponed.")
            self.update_status()

    def delete_cleanup_candidates(self, candidates):
        result = delete_cleanup_items(candidates)

        print(f"Deleted: {result['deleted']} | Failed: {result['failed']}")
        self.update_status()

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    tray = ArtemisTray()
    tray.run()