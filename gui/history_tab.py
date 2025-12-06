from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

import os
from core.history_manager import HistoryManager


SPOTIFY_BG = "#0F0F0F"
ROW_BG = "#1B1B1B"
ROW_HOVER = "#232323"
TEXT_COLOR = "#FFFFFF"
SUBTEXT_COLOR = "#AAAAAA"
ACCENT = "#5865F2"  # Discord blurple


class HistoryRow(QWidget):
    """One Spotify-style track history row."""

    def __init__(self, record, delete_callback):
        super().__init__()

        self.record = record
        self.delete_callback = delete_callback

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Thumbnail (placeholder)
        thumb = QLabel()
        pix = QPixmap(40, 40)
        pix.fill(Qt.GlobalColor.darkGray)
        thumb.setPixmap(pix)
        layout.addWidget(thumb)

        # Title + metadata
        text_col = QVBoxLayout()
        title = QLabel(f"{os.path.basename(record['flac'])}")
        title.setStyleSheet(f"color: {TEXT_COLOR}; font-weight: bold;")

        sub = QLabel(
            f"{record['metadata'].get('ARTIST', 'Unknown Artist')} — "
            f"{record['metadata'].get('ALBUM', 'Unknown Album')}"
        )
        sub.setStyleSheet(f"color: {SUBTEXT_COLOR}; font-size: 11px;")

        text_col.addWidget(title)
        text_col.addWidget(sub)

        layout.addLayout(text_col, 4)

        # Size info
        before_mb = record['size_before'] / (1024 * 1024)
        after_mb = record['size_after'] / (1024 * 1024)
        saved = before_mb - after_mb

        size_label = QLabel(f"{before_mb:.1f} → {after_mb:.1f} MB")
        size_label.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(size_label, 1)

        # Date
        date_label = QLabel(record["date"])
        date_label.setStyleSheet(f"color: {SUBTEXT_COLOR}; font-size: 11px;")
        layout.addWidget(date_label, 1)

        # Delete button
        btn_delete = QPushButton("Delete")
        btn_delete.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #8B0000;
                color: white;
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: #B30000;
            }}
            """
        )
        btn_delete.clicked.connect(self.on_delete)
        layout.addWidget(btn_delete)

        self.setLayout(layout)
        self.setStyleSheet(f"background-color: {ROW_BG};")

    def enterEvent(self, event):
        self.setStyleSheet(f"background-color: {ROW_HOVER};")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(f"background-color: {ROW_BG};")
        super().leaveEvent(event)

    def on_delete(self):
        """Call HistoryManager delete function"""
        self.delete_callback(self.record)


class HistoryTab(QWidget):

    def __init__(self):
        super().__init__()

        self.manager = HistoryManager()

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # ----------------------------
        # Search bar
        # ----------------------------
        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search history...")
        self.search_box.textChanged.connect(self.refresh)

        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self.clear_all)

        search_row.addWidget(self.search_box)
        search_row.addWidget(btn_clear)

        layout.addLayout(search_row)

        # ----------------------------
        # List widget
        # ----------------------------
        self.list = QListWidget()
        layout.addWidget(self.list)

        self.setLayout(layout)

        self.refresh()

    # --------------------------------------------------------------
    def refresh(self):
        """Reloads history list."""
        text = self.search_box.text().lower()
        self.list.clear()

        records = self.manager.load_all()
        self.full_records = records

        for rec in records:
            if text and text not in rec["flac"].lower():
                continue

            row = HistoryRow(rec, self.delete_single)

            item = QListWidgetItem(self.list)
            item.setSizeHint(row.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, row)

    # --------------------------------------------------------------
    def delete_single(self, record):
        """Delete one entry from history.json"""
        confirm = QMessageBox.question(
            self, "Delete Entry",
            f"Remove this entry:\n\n{record['flac']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        records = self.manager.load_all()
        new_list = [r for r in records if r != record]
        self.manager._save(new_list)

        self.refresh()

    # --------------------------------------------------------------
    def clear_all(self):
        confirm = QMessageBox.question(
            self, "Clear All History",
            "Are you sure you want to delete ALL history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.manager.clear()
            self.refresh()
