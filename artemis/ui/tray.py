import json
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtCore import Qt, QTimer, QItemSelectionModel
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QSystemTrayIcon,
)

from artemis.core.cleanup_tracker import (
    get_cleanup_candidates,
    get_cleanup_stats,
    postpone_cleanup_items,
    delete_cleanup_items,
)
from scripts.python.artemis_control import (
    get_artemis_activity,
    is_artemis_running,
    start_artemis,
    stop_artemis,
)


CONFIG_PATH = ROOT_DIR / "config" / "downloads_sorter.json"

APP_VERSION = "v0.4.4"
DEVELOPER_NAME = "Marius Cuzman"
ARTEMIS_ACCENT = "#64d6d2"


def load_sorter_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}

    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def format_size(size_bytes: int) -> str:
    try:
        size_bytes = int(size_bytes)
    except Exception:
        return "0 MB"

    mb = size_bytes / (1024 * 1024)

    if mb >= 1024:
        return f"{mb / 1024:.1f} GB"

    return f"{mb:.1f} MB"


def open_path_in_explorer(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(str(path))
    except Exception:
        subprocess.Popen(["explorer", str(path)])


class ArtemisMainWindow(QMainWindow):
    TAB_PROCESSES = 0
    TAB_CLEANUP = 1
    TAB_CUSTOMIZE = 2
    TAB_SETTINGS = 3
    TAB_ABOUT = 4

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Artemis Toolkit")
        self.setMinimumSize(940, 580)

        self.current_cleanup_candidates = []

        self.setStyleSheet("""
            QMainWindow {
                background-color: #202020;
                color: #f2f2f2;
            }

            QLabel {
    background-color: transparent;
}
            
            QWidget {
    color: #f2f2f2;
    font-size: 14px;
}

QLabel {
    background-color: transparent;
}

QMainWindow {
    background-color: #202020;
    color: #f2f2f2;
}

            QLabel#TitleLabel {
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#SectionTitle {
                font-size: 18px;
                font-weight: 600;
                margin-top: 8px;
                margin-bottom: 6px;
            }

            QLabel#MutedLabel {
    color: #b0b0b0;
    background-color: transparent;
    padding: 2px 0px;
}

            QFrame#Sidebar {
                background-color: #181818;
                border-right: 1px solid #333333;
            }

            QPushButton {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 8px;
                padding: 8px 12px;
                text-align: left;
            }

            QPushButton:hover {
                background-color: #3f3f3f;
            }

            QPushButton:disabled {
                color: #777777;
                background-color: #292929;
                border: 1px solid #383838;
            }

            QPushButton#SidebarButton {
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 10px 14px;
                font-size: 15px;
            }

            QPushButton#SidebarButtonActive {
                background-color: #2f3d3d;
                border: none;
                border-left: 4px solid __ACCENT__;
                border-radius: 8px;
                text-align: left;
                padding: 10px 14px 10px 16px;
                font-size: 15px;
                color: #ffffff;
            }

            QPushButton#DonateButton {
                background-color: __ACCENT__;
                color: #101010;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 700;
                text-align: center;
            }

            QPushButton#DonateButton:hover {
                background-color: #7be7e3;
            }

            QFrame#Card {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 14px;
            }

            QFrame#SettingRow {
                background-color: #242424;
                border: 1px solid #363636;
                border-radius: 10px;
            }

            QTableWidget {
                background-color: #252525;
                alternate-background-color: #2c2c2c;
                gridline-color: #3a3a3a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                selection-background-color: #2f4a4a;
                selection-color: #ffffff;
            }

            QHeaderView::section {
                background-color: #303030;
                color: #f2f2f2;
                padding: 6px;
                border: none;
                border-right: 1px solid #444444;
            }

            QTableWidget::item {
                padding: 6px;
            }

            QLineEdit {
                background-color: #303030;
                color: #f2f2f2;
                border: 1px solid #444444;
                border-radius: 8px;
                padding: 7px 10px;
            }

            QLineEdit:disabled {
                color: #b0b0b0;
                background-color: #292929;
                border: 1px solid #3a3a3a;
            }

            QCheckBox {
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 38px;
                height: 20px;
            }
        """.replace("__ACCENT__", ARTEMIS_ACCENT))

        root = QWidget()
        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root.setLayout(root_layout)
        self.setCentralWidget(root)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(210)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(14, 18, 14, 14)
        sidebar_layout.setSpacing(8)
        self.sidebar.setLayout(sidebar_layout)

        app_title = QLabel("☾  Artemis Toolkit")
        app_title.setStyleSheet("font-size: 16px; font-weight: 600; margin-bottom: 24px;")
        sidebar_layout.addWidget(app_title)

        self.btn_processes = self.create_sidebar_button("Processes", self.TAB_PROCESSES)
        self.btn_cleanup = self.create_sidebar_button("Cleanup", self.TAB_CLEANUP)
        self.btn_customize = self.create_sidebar_button("Customize", self.TAB_CUSTOMIZE)
        self.btn_settings = self.create_sidebar_button("Settings", self.TAB_SETTINGS)
        self.btn_about = self.create_sidebar_button("About", self.TAB_ABOUT)

        sidebar_layout.addWidget(self.btn_processes)
        sidebar_layout.addWidget(self.btn_cleanup)
        sidebar_layout.addWidget(self.btn_customize)
        sidebar_layout.addWidget(self.btn_settings)
        sidebar_layout.addWidget(self.btn_about)
        sidebar_layout.addStretch()

        self.pages = QStackedWidget()

        self.processes_page = self.build_processes_page()
        self.cleanup_page = self.build_cleanup_page()
        self.customize_page = self.build_customize_page()
        self.settings_page = self.build_settings_page()
        self.about_page = self.build_about_page()

        self.pages.addWidget(self.processes_page)
        self.pages.addWidget(self.cleanup_page)
        self.pages.addWidget(self.customize_page)
        self.pages.addWidget(self.settings_page)
        self.pages.addWidget(self.about_page)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.pages)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_dynamic_data)
        self.refresh_timer.start(1000)

        self.switch_tab(self.TAB_PROCESSES)
        self.refresh_dynamic_data()

    def create_sidebar_button(self, text: str, tab_index: int) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("SidebarButton")
        button.clicked.connect(lambda: self.switch_tab(tab_index))
        return button

    def switch_tab(self, tab_index: int):
        self.pages.setCurrentIndex(tab_index)

        buttons = [
            self.btn_processes,
            self.btn_cleanup,
            self.btn_customize,
            self.btn_settings,
            self.btn_about,
        ]

        for index, button in enumerate(buttons):
            if index == tab_index:
                button.setObjectName("SidebarButtonActive")
            else:
                button.setObjectName("SidebarButton")

            button.style().unpolish(button)
            button.style().polish(button)

        if tab_index == self.TAB_CUSTOMIZE:
            self.refresh_rules_table()

        if tab_index == self.TAB_CLEANUP:
            self.refresh_cleanup_table()

        if tab_index == self.TAB_SETTINGS:
            self.refresh_settings_preview()

    def make_page(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(16)
        page.setLayout(layout)

        title_label = QLabel(title)
        title_label.setObjectName("TitleLabel")
        layout.addWidget(title_label)

        return page, layout

    def make_card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        card.setLayout(layout)

        return card, layout

    def configure_table(self, table: QTableWidget):
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setWordWrap(False)
        table.verticalHeader().setVisible(False)
    def restore_table_row_selection(self, table: QTableWidget, rows: list[int]) -> None:
        table.clearSelection()

        selection_model = table.selectionModel()

        if selection_model is None:
            return

        for row in rows:
            if row < 0 or row >= table.rowCount():
                continue

            index = table.model().index(row, 0)
            selection_model.select(
                index,
                QItemSelectionModel.SelectionFlag.Select
                | QItemSelectionModel.SelectionFlag.Rows,
            )
    # -------------------------
    # Processes page
    # -------------------------

    def build_processes_page(self) -> QWidget:
        page, layout = self.make_page("Processes")

        status_title = QLabel("Current Status")
        status_title.setObjectName("SectionTitle")
        layout.addWidget(status_title)

        status_card, status_layout = self.make_card()

        self.status_label = QLabel("Status: unknown")
        self.status_label.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.activity_label = QLabel("Activity: unknown")
        self.activity_label.setObjectName("MutedLabel")

        self.start_stop_button = QPushButton("Start Sorter")
        self.start_stop_button.setFixedWidth(160)
        self.start_stop_button.clicked.connect(self.toggle_sorter)

        status_top = QHBoxLayout()
        status_top.addWidget(self.status_label)
        status_top.addStretch()
        status_top.addWidget(self.start_stop_button)

        status_layout.addLayout(status_top)
        status_layout.addWidget(self.activity_label)

        layout.addWidget(status_card)

        recent_title = QLabel("Recent Activity")
        recent_title.setObjectName("SectionTitle")
        layout.addWidget(recent_title)

        recent_card, recent_layout = self.make_card()
        recent_note = QLabel("Recent moved files will be shown here later.")
        recent_note.setObjectName("MutedLabel")
        recent_layout.addWidget(recent_note)

        layout.addWidget(recent_card)

        open_sorted_button = QPushButton("Open Sorted Folder")
        open_sorted_button.setFixedWidth(180)
        open_sorted_button.clicked.connect(self.open_sorted_folder)
        layout.addWidget(open_sorted_button)

        layout.addStretch()

        return page

    def toggle_sorter(self):
        if is_artemis_running():
            stop_artemis()
        else:
            start_artemis()

        self.refresh_dynamic_data()

    # -------------------------
    # Cleanup page
    # -------------------------

    def build_cleanup_page(self) -> QWidget:
        page, layout = self.make_page("Cleanup")

        summary_card, summary_layout = self.make_card()

        self.cleanup_summary_label = QLabel("Cleanup: unknown")
        self.cleanup_summary_label.setStyleSheet("font-size: 17px; font-weight: 600;")

        cleanup_hint = QLabel("Select rows, then delete or postpone selected cleanup candidates.")
        cleanup_hint.setObjectName("MutedLabel")

        summary_layout.addWidget(self.cleanup_summary_label)
        summary_layout.addWidget(cleanup_hint)

        layout.addWidget(summary_card)

        self.cleanup_table = QTableWidget()
        self.cleanup_table.setColumnCount(4)
        self.cleanup_table.setHorizontalHeaderLabels(["File", "Size", "Reason", "Path"])
        self.configure_table(self.cleanup_table)

        self.cleanup_table.setMinimumHeight(300)

        cleanup_header = self.cleanup_table.horizontalHeader()
        cleanup_header.setStretchLastSection(False)
        cleanup_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cleanup_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        cleanup_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        cleanup_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.cleanup_table, 1)

        button_row = QHBoxLayout()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_cleanup_table)

        delete_button = QPushButton("Delete selected")
        delete_button.clicked.connect(self.delete_selected_cleanup_items)

        postpone_button = QPushButton("Postpone selected")
        postpone_button.clicked.connect(self.postpone_selected_cleanup_items)

        button_row.addWidget(refresh_button)
        button_row.addWidget(delete_button)
        button_row.addWidget(postpone_button)
        button_row.addStretch()

        layout.addLayout(button_row)

        return page

    def get_selected_cleanup_paths_from_table(self) -> set[str]:
        selected_rows = self.cleanup_table.selectionModel().selectedRows()
        paths = set()

        for index in selected_rows:
            path_item = self.cleanup_table.item(index.row(), 3)
            if path_item:
                paths.add(path_item.text())

        return paths

    def refresh_cleanup_table(self):
        selected_paths = self.get_selected_cleanup_paths_from_table()

        candidates = get_cleanup_candidates()
        self.current_cleanup_candidates = candidates

        cleanup_count, cleanup_size = get_cleanup_stats()
        candidate_count = len(candidates)

        self.cleanup_summary_label.setText(
            f"Queue: {cleanup_count} item(s), {format_size(cleanup_size)} | "
            f"Ready for review: {candidate_count}"
        )

        self.cleanup_table.setRowCount(0)

        rows_to_restore = []

        for row, item in enumerate(candidates):
            path_text = item.get("path", "")
            path = Path(path_text)
            size = item.get("size", 0)
            reason = item.get("reason", "")

            self.cleanup_table.insertRow(row)
            self.cleanup_table.setItem(row, 0, QTableWidgetItem(path.name))
            self.cleanup_table.setItem(row, 1, QTableWidgetItem(format_size(size)))
            self.cleanup_table.setItem(row, 2, QTableWidgetItem(str(reason)))
            self.cleanup_table.setItem(row, 3, QTableWidgetItem(path_text))

            if path_text in selected_paths:
                rows_to_restore.append(row)

        self.restore_table_row_selection(self.cleanup_table, rows_to_restore)

    def get_selected_cleanup_candidates(self) -> list[dict]:
        selected_rows = sorted(
            index.row()
            for index in self.cleanup_table.selectionModel().selectedRows()
        )

        return [
            self.current_cleanup_candidates[row]
            for row in selected_rows
            if row < len(self.current_cleanup_candidates)
        ]

    def delete_selected_cleanup_items(self):
        selected = self.get_selected_cleanup_candidates()

        if not selected:
            QMessageBox.information(self, "Artemis Cleanup", "Select at least one cleanup item first.")
            return

        result = QMessageBox.question(
            self,
            "Confirm deletion",
            f"Delete {len(selected)} selected file(s)?\n\nThis cannot be undone.",
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        delete_result = delete_cleanup_items(selected)

        QMessageBox.information(
            self,
            "Cleanup complete",
            f"Deleted: {delete_result['deleted']}\nFailed: {delete_result['failed']}",
        )

        self.refresh_cleanup_table()

    def postpone_selected_cleanup_items(self):
        selected = self.get_selected_cleanup_candidates()

        if not selected:
            QMessageBox.information(self, "Artemis Cleanup", "Select at least one cleanup item first.")
            return

        paths = [item.get("path", "") for item in selected]
        postpone_cleanup_items(paths)

        self.refresh_cleanup_table()

    # -------------------------
    # Customize page
    # -------------------------

    def build_customize_page(self) -> QWidget:
        page, layout = self.make_page("Customize")

        info_card, info_layout = self.make_card()

        info_label = QLabel("User rules from downloads_sorter.json")
        info_label.setStyleSheet("font-size: 17px; font-weight: 600;")

        info_hint = QLabel("This sprint only displays existing rules. Rule creation/editing comes later.")
        info_hint.setObjectName("MutedLabel")

        info_layout.addWidget(info_label)
        info_layout.addWidget(info_hint)

        layout.addWidget(info_card)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(5)
        self.rules_table.setHorizontalHeaderLabels(["Enabled", "Name", "Match", "Action", "Destination"])
        self.configure_table(self.rules_table)

        self.rules_table.setMinimumHeight(300)

        rules_header = self.rules_table.horizontalHeader()
        rules_header.setStretchLastSection(False)
        rules_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        rules_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        rules_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        rules_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        rules_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.rules_table, 1)

        button_row = QHBoxLayout()

        refresh_button = QPushButton("Refresh rules")
        refresh_button.clicked.connect(self.refresh_rules_table)

        add_button = QPushButton("Add rule later")
        add_button.setEnabled(False)

        edit_button = QPushButton("Edit later")
        edit_button.setEnabled(False)

        delete_button = QPushButton("Delete later")
        delete_button.setEnabled(False)

        button_row.addWidget(refresh_button)
        button_row.addWidget(add_button)
        button_row.addWidget(edit_button)
        button_row.addWidget(delete_button)
        button_row.addStretch()

        layout.addLayout(button_row)

        return page

    def get_selected_rule_ids_from_table(self) -> set[str]:
        selected_rows = self.rules_table.selectionModel().selectedRows()
        rule_ids = set()

        for index in selected_rows:
            id_item = self.rules_table.item(index.row(), 0)

            if id_item:
                rule_id = id_item.data(Qt.ItemDataRole.UserRole)

                if rule_id:
                    rule_ids.add(str(rule_id))

        return rule_ids

    def refresh_rules_table(self):
        selected_rule_ids = self.get_selected_rule_ids_from_table()

        config = load_sorter_config()
        user_rules = config.get("user_rules", {})
        rules = user_rules.get("rules", [])

        if not isinstance(rules, list):
            rules = []

        self.rules_table.setRowCount(0)

        rows_to_restore = []
        visible_row = 0

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            rule_id = rule.get("id", "")
            enabled = rule.get("enabled", True)
            name = rule.get("name", "Unnamed rule")

            match = rule.get("match", {})
            action = rule.get("action", {})

            match_type = match.get("type", "")
            match_value = match.get("value", "")
            action_type = action.get("type", "")
            destination = action.get("destination", "")

            enabled_item = QTableWidgetItem("Yes" if enabled else "No")
            enabled_item.setData(Qt.ItemDataRole.UserRole, str(rule_id))

            self.rules_table.insertRow(visible_row)

            self.rules_table.setItem(visible_row, 0, enabled_item)
            self.rules_table.setItem(visible_row, 1, QTableWidgetItem(str(name)))
            self.rules_table.setItem(visible_row, 2, QTableWidgetItem(f"{match_type}: {match_value}"))
            self.rules_table.setItem(visible_row, 3, QTableWidgetItem(str(action_type)))
            self.rules_table.setItem(visible_row, 4, QTableWidgetItem(str(destination)))

            if str(rule_id) in selected_rule_ids:
                rows_to_restore.append(visible_row)

            visible_row += 1

        self.restore_table_row_selection(self.rules_table, rows_to_restore)

    # -------------------------
    # Settings page
    # -------------------------

    def build_settings_page(self) -> QWidget:
        page, layout = self.make_page("Settings")

        settings_card, settings_layout = self.make_card()

        self.settings_summary_label = QLabel("Editable settings preview")
        self.settings_summary_label.setStyleSheet("font-size: 17px; font-weight: 600;")

        settings_hint = QLabel("Controls are placeholders for now. They show the future layout without saving changes yet.")
        settings_hint.setObjectName("MutedLabel")

        settings_layout.addWidget(self.settings_summary_label)
        settings_layout.addWidget(settings_hint)

        self.process_existing_toggle = QCheckBox("On")
        self.process_existing_toggle.setEnabled(False)

        self.cleanup_age_input = QLineEdit()
        self.cleanup_age_input.setFixedWidth(120)
        self.cleanup_age_input.setEnabled(False)

        self.cleanup_size_input = QLineEdit()
        self.cleanup_size_input.setFixedWidth(120)
        self.cleanup_size_input.setEnabled(False)

        self.archive_extensions_input = QLineEdit()
        self.archive_extensions_input.setEnabled(False)

        settings_layout.addWidget(
            self.make_setting_row("Process existing files on startup", self.process_existing_toggle)
        )
        settings_layout.addWidget(
            self.make_setting_row("Cleanup reminder age", self.cleanup_age_input)
        )
        settings_layout.addWidget(
            self.make_setting_row("Cleanup minimum total size", self.cleanup_size_input)
        )
        settings_layout.addWidget(
            self.make_setting_row("Archive extensions", self.archive_extensions_input)
        )

        save_row = QHBoxLayout()

        self.save_settings_button = QPushButton("Save settings later")
        self.save_settings_button.setEnabled(False)
        self.save_settings_button.setFixedWidth(170)

        save_row.addWidget(self.save_settings_button)
        save_row.addStretch()

        settings_layout.addLayout(save_row)

        layout.addWidget(settings_card)

        open_sorted_button = QPushButton("Open Sorted Folder")
        open_sorted_button.setFixedWidth(180)
        open_sorted_button.clicked.connect(self.open_sorted_folder)

        layout.addWidget(open_sorted_button)
        layout.addStretch()

        return page

    def make_setting_row(self, label_text: str, control: QWidget) -> QFrame:
        row_frame = QFrame()
        row_frame.setObjectName("SettingRow")

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(14, 10, 14, 10)
        row_layout.setSpacing(12)
        row_frame.setLayout(row_layout)

        label = QLabel(label_text)
        label.setStyleSheet("font-weight: 600;")

        row_layout.addWidget(label)
        row_layout.addStretch()
        row_layout.addWidget(control)

        return row_frame

    def refresh_settings_preview(self):
        config = load_sorter_config()

        process_existing = config.get("process_existing_on_startup", True)
        cleanup = config.get("cleanup", {})
        archive_extensions = config.get("archive_extensions", [])

        min_age_seconds = cleanup.get("min_age_seconds", 0)
        min_age_days = round(min_age_seconds / 86400, 1) if min_age_seconds else "unknown"

        min_total_size_mb = cleanup.get("min_total_size_mb", "unknown")

        self.process_existing_toggle.setChecked(bool(process_existing))
        self.process_existing_toggle.setText("On" if process_existing else "Off")

        self.cleanup_age_input.setText(f"{min_age_days} day(s)")
        self.cleanup_size_input.setText(f"{min_total_size_mb} MB")
        self.archive_extensions_input.setText(", ".join(archive_extensions))

    # -------------------------
    # About page
    # -------------------------

    def build_about_page(self) -> QWidget:
        page, layout = self.make_page("About")

        about_card, about_layout = self.make_card()

        title = QLabel("Artemis Toolkit")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")

        pitch = QLabel(
            "Turn it on once, your Downloads folder sorts itself, "
            "and you get nudged to clean up files you do not use."
        )
        pitch.setObjectName("MutedLabel")
        pitch.setWordWrap(True)

        version_label = QLabel(f"Version: {APP_VERSION}")
        developer_label = QLabel(f"Developer: {DEVELOPER_NAME}")

        for label in [version_label, developer_label]:
            label.setObjectName("MutedLabel")

        about_layout.addWidget(title)
        about_layout.addWidget(pitch)
        about_layout.addSpacing(8)
        about_layout.addWidget(version_label)
        about_layout.addWidget(developer_label)

        button_row = QHBoxLayout()

        github_button = QPushButton("GitHub later")
        github_button.clicked.connect(lambda: self.show_placeholder_link("GitHub"))

        reddit_button = QPushButton("Reddit later")
        reddit_button.clicked.connect(lambda: self.show_placeholder_link("Reddit"))

        donate_button = QPushButton("Donate")
        donate_button.setObjectName("DonateButton")
        donate_button.clicked.connect(lambda: self.show_placeholder_link("Donate"))

        button_row.addWidget(github_button)
        button_row.addWidget(reddit_button)
        button_row.addWidget(donate_button)
        button_row.addStretch()

        about_layout.addSpacing(10)
        about_layout.addLayout(button_row)

        layout.addWidget(about_card)
        layout.addStretch()

        return page

    def show_placeholder_link(self, name: str):
        QMessageBox.information(
            self,
            "Artemis",
            f"{name} link is not configured yet.",
        )

    # -------------------------
    # Shared refresh / window behavior
    # -------------------------

    def refresh_dynamic_data(self):
        running = is_artemis_running()
        activity = get_artemis_activity()

        state = activity.get("state", "idle")
        message = activity.get("message", "")

        if running:
            self.status_label.setText(f"● Sorter running — {state}")
            self.status_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #57d26a;")
            self.start_stop_button.setText("Stop Sorter")
        else:
            self.status_label.setText("● Sorter stopped")
            self.status_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #d65f5f;")
            self.start_stop_button.setText("Start Sorter")

        self.activity_label.setText(f"Activity: {message or 'No current activity'}")

        if self.pages.currentIndex() == self.TAB_CLEANUP:
            self.refresh_cleanup_table()

        if self.pages.currentIndex() == self.TAB_SETTINGS:
            self.refresh_settings_preview()

    def open_sorted_folder(self):
        config = load_sorter_config()
        destination_root = config.get("destination_root", "")

        if not destination_root:
            QMessageBox.warning(self, "Artemis", "No destination_root found in config.")
            return

        open_path_in_explorer(Path(destination_root))

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class ArtemisTray:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        icon_dir = ROOT_DIR / "icons"

        self.icon_idle = QIcon(str(icon_dir / "idle.png"))
        self.icon_active = QIcon(str(icon_dir / "active.png"))
        self.icon_warning = QIcon(str(icon_dir / "warning.png"))
        self.icon_error = QIcon(str(icon_dir / "error.png"))

        self.window = ArtemisMainWindow()

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon_idle)
        self.tray.setToolTip("Artemis - Idle")
        self.tray.setVisible(True)

        self.build_tray_menu()

        self.tray.activated.connect(self.on_tray_click)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

        self.update_status()

    def build_tray_menu(self):
        menu = QMenu()

        open_action = menu.addAction("Open Artemis")
        open_action.triggered.connect(lambda: self.open_window(ArtemisMainWindow.TAB_PROCESSES))

        menu.addSeparator()

        processes_action = menu.addAction("Processes")
        processes_action.triggered.connect(lambda: self.open_window(ArtemisMainWindow.TAB_PROCESSES))

        cleanup_action = menu.addAction("Cleanup")
        cleanup_action.triggered.connect(lambda: self.open_window(ArtemisMainWindow.TAB_CLEANUP))

        customize_action = menu.addAction("Customize")
        customize_action.triggered.connect(lambda: self.open_window(ArtemisMainWindow.TAB_CUSTOMIZE))

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(lambda: self.open_window(ArtemisMainWindow.TAB_SETTINGS))

        about_action = menu.addAction("About")
        about_action.triggered.connect(lambda: self.open_window(ArtemisMainWindow.TAB_ABOUT))

        menu.addSeparator()

        open_sorted_action = menu.addAction("Open Sorted Folder")
        open_sorted_action.triggered.connect(self.window.open_sorted_folder)

        menu.addSeparator()

        exit_action = menu.addAction("Exit Artemis UI")
        exit_action.triggered.connect(self.app.quit)

        self.tray.setContextMenu(menu)

    def open_window(self, tab_index: int | None = None):
        if tab_index is not None:
            self.window.switch_tab(tab_index)

        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

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

        if not running:
            self.tray.setIcon(self.icon_error)
            self.tray.setToolTip(f"Artemis - Sorter stopped{cleanup_text}")
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
                f"Artemis - Review needed: {candidate_count} item(s)"
            )
            return

        self.tray.setIcon(self.icon_idle)
        self.tray.setToolTip(f"Artemis - Idle{cleanup_text}")

    def on_tray_click(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.open_window()

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    tray = ArtemisTray()
    tray.run()