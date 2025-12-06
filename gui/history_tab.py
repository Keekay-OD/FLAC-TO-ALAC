from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QProgressBar, QLineEdit, QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt

from core.history_manager import HistoryManager
from core.event_bus import event_bus
import os

# Colors
SPOTIFY_GREEN = "#1DB954"
ROW_BG = "#1F1F1F"
ROW_HOVER = "#2A2A2A"
TEXT = "#E6E6E6"
SUBTEXT = "#A0A0A0"


class HistoryRow(QWidget):
    def __init__(self, record, delete_callback):
        super().__init__()
        self.record = record
        self.delete_callback = delete_callback

        self.setFixedHeight(55)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        # Thumbnail placeholder
        thumb = QLabel()
        thumb.setFixedSize(40, 40)
        thumb.setStyleSheet("background-color: #3A3A3A; border-radius: 6px;")
        layout.addWidget(thumb)

        # Only show filename (no album, no artist)
        text_col = QVBoxLayout()

        title = QLabel(os.path.basename(record["flac"]))
        title.setStyleSheet("""
            color: #FFFFFF;
            font-size: 15px;
            font-weight: bold;
        """)

        text_col.addWidget(title)
        layout.addLayout(text_col, 3)

        # Size info
        before_mb = record["size_before"] / (1024 * 1024)
        after_mb = record["size_after"] / (1024 * 1024)

        size_label = QLabel(f"{before_mb:.1f} → {after_mb:.1f} MB")
        size_label.setStyleSheet("color: #CCCCCC; font-size: 13px;")
        layout.addWidget(size_label)

        # Date
        date_label = QLabel(record["date"])
        date_label.setStyleSheet("color: #999999; font-size: 12px;")
        layout.addWidget(date_label)

        # Delete button
        btn_delete = QPushButton("✕")
        btn_delete.setFixedWidth(32)
        btn_delete.clicked.connect(lambda: delete_callback(record["id"]))
        btn_delete.setStyleSheet("""
            QPushButton {
                background: #AA2222;
                color: white;
                font-size: 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background: #CC2222; }
        """)
        layout.addWidget(btn_delete)

        # Progress bar (small underline)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(5)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #333;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 3px;
            }
        """)

        root = QVBoxLayout()
        root.addLayout(layout)
        root.addWidget(self.progress)

        self.setLayout(root)
        self.setStyleSheet("background-color: #1E1E1E; border-radius: 6px;")

    def set_progress(self, value):
        self.progress.setValue(value)

    def enterEvent(self, event):
        self.setStyleSheet("background-color: #2A2A2A; border-radius: 6px;")
    def leaveEvent(self, event):
        self.setStyleSheet("background-color: #1E1E1E; border-radius: 6px;")


class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()

        self.manager = HistoryManager()

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Search bar + buttons
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search history...")
        self.search.textChanged.connect(self.refresh)
        search_row.addWidget(self.search)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh)
        search_row.addWidget(btn_refresh)

        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self.clear_all)
        search_row.addWidget(btn_clear)

        layout.addLayout(search_row)

        # List
        self.list = QListWidget()
        self.list.setSpacing(6)
        layout.addWidget(self.list)

        self.setLayout(layout)

        # Progress listeners (live updates for currently converting)
        event_bus.progress_updated.connect(self.on_progress)
        event_bus.conversion_finished.connect(self.on_finished)

        self.rows = {}
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

            self.rows[rec["flac"]] = row

    # --------------------------------------------------------
    def on_progress(self, flac_path, percent):
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
            self, "Delete Entry", "Remove this history item?",
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
