from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QProgressBar, QLineEdit, QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt

from core.history_manager import HistoryManager
from core.event_bus import event_bus

import os


SPOTIFY_GREEN = "#1DB954"
ROW_BG = "#1A1A1A"
ROW_HOVER = "#222222"
TEXT = "#FFFFFF"
SUBTEXT = "#999999"


class HistoryRow(QWidget):
    def __init__(self, record, delete_callback):
        super().__init__()
        self.record = record
        self.delete_callback = delete_callback

        self.setFixedHeight(36)

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(10)

        # Small 32px thumbnail placeholder
        thumb = QLabel()
        thumb.setFixedSize(32, 32)
        thumb.setStyleSheet("background-color: #333; border-radius: 4px;")
        layout.addWidget(thumb)

        # Title + artist inline
        text_col = QVBoxLayout()
        title = QLabel(os.path.basename(record["flac"]))
        title.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: bold;")

        sub = QLabel(f"{record['artist']} — {record['album']}")
        sub.setStyleSheet(f"color: {SUBTEXT}; font-size: 11px;")

        text_col.addWidget(title)
        text_col.addWidget(sub)
        layout.addLayout(text_col, 2)

        # Size info
        before_mb = record["size_before"] / (1024 * 1024)
        after_mb = record["size_after"] / (1024 * 1024)

        size_label = QLabel(f"{before_mb:.1f} → {after_mb:.1f} MB")
        size_label.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
        layout.addWidget(size_label)

        # Date
        date_label = QLabel(record["date"])
        date_label.setStyleSheet(f"color: {SUBTEXT}; font-size: 11px;")
        layout.addWidget(date_label)

        # Delete
        btn_delete = QPushButton("✕")
        btn_delete.setFixedWidth(28)
        btn_delete.clicked.connect(lambda: delete_callback(record["id"]))
        btn_delete.setStyleSheet(
            """
            QPushButton {
                background: #7A0000;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #AA0000; }
            """
        )
        layout.addWidget(btn_delete)

        # Progress bar (hidden until conversion update)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)  # default done
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {SPOTIFY_GREEN};
            }}
            QProgressBar {{
                background: #333;
                border: none;
            }}
        """)

        root = QVBoxLayout()
        root.addLayout(layout)
        root.addWidget(self.progress)

        self.setLayout(root)
        self.setStyleSheet(f"background-color: {ROW_BG}; border-radius: 4px;")

    def set_progress(self, value):
        self.progress.setValue(value)

    def enterEvent(self, event):
        self.setStyleSheet(f"background-color: {ROW_HOVER}; border-radius: 4px;")
    def leaveEvent(self, event):
        self.setStyleSheet(f"background-color: {ROW_BG}; border-radius: 4px;")


class HistoryTab(QWidget):

    def __init__(self):
        super().__init__()

        self.manager = HistoryManager()

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Search bar
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")
        self.search.textChanged.connect(self.refresh)
        search_row.addWidget(self.search)

        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self.clear_all)
        search_row.addWidget(btn_clear)

        layout.addLayout(search_row)

        # List
        self.list = QListWidget()
        self.list.setSpacing(4)
        layout.addWidget(self.list)

        self.setLayout(layout)

        # LIVE PROGRESS EVENT LISTENERS
        event_bus.progress_updated.connect(self.on_progress)
        event_bus.conversion_finished.connect(self.on_finished)

        self.rows = {}  # flac_path → HistoryRow
        self.refresh()

    # --------------------------------------------------------
    def refresh(self):
        """Reload history list from DB."""
        query = self.search.text().lower()

        records = self.manager.load_all()

        self.list.clear()
        self.rows.clear()

        for rec in records:
            if query and query not in rec["flac"].lower():
                continue

            row = HistoryRow(rec, self.delete_one)
            item = QListWidgetItem(self.list)
            item.setSizeHint(row.sizeHint())

            self.list.addItem(item)
            self.list.setItemWidget(item, row)

            # Link for live updates
            self.rows[rec["flac"]] = row

    # --------------------------------------------------------
    def on_progress(self, flac_path, percent):
        """Update row progress bar."""
        row = self.rows.get(flac_path)
        if row:
            row.set_progress(percent)

    def on_finished(self, flac_path, success):
        row = self.rows.get(flac_path)
        if row:
            row.set_progress(100)

    # --------------------------------------------------------
    def delete_one(self, row_id):
        confirm = QMessageBox.question(
            self, "Delete Entry", "Remove this item from history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.manager.delete(row_id)
            self.refresh()

    # --------------------------------------------------------
    def clear_all(self):
        confirm = QMessageBox.question(
            self, "Clear All History",
            "Delete ALL history entries?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.manager.clear()
            self.refresh()
