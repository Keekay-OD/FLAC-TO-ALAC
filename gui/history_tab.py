import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt

from core.history_manager import HistoryManager


class HistoryTab(QWidget):

    def __init__(self):
        super().__init__()

        self.history = HistoryManager()

        layout = QVBoxLayout()

        # -------------------------
        # Search + Filters
        # -------------------------
        filter_layout = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search…")

        self.filter_artist = QLineEdit()
        self.filter_artist.setPlaceholderText("Filter Artist")

        self.filter_album = QLineEdit()
        self.filter_album.setPlaceholderText("Filter Album")

        self.filter_status = QComboBox()
        self.filter_status.addItems(["", "success", "failed"])

        btn_refresh = QPushButton("Refresh")
        btn_export = QPushButton("Export CSV")
        btn_clear = QPushButton("Clear History")

        filter_layout.addWidget(self.search_bar)
        filter_layout.addWidget(self.filter_artist)
        filter_layout.addWidget(self.filter_album)
        filter_layout.addWidget(self.filter_status)
        filter_layout.addWidget(btn_refresh)
        filter_layout.addWidget(btn_export)
        filter_layout.addWidget(btn_clear)

        layout.addLayout(filter_layout)

        # -------------------------
        # Table
        # -------------------------
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "FLAC", "ALAC", "Artist", "Album", "Track",
            "Size Before", "Size After", "Date", "Status"
        ])
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)

        # Events
        btn_refresh.clicked.connect(self.load_history)
        btn_export.clicked.connect(self.export_csv)
        btn_clear.clicked.connect(self.clear_history)

        self.table.cellDoubleClicked.connect(self.open_folder)
        self.search_bar.textChanged.connect(self.load_history)
        self.filter_artist.textChanged.connect(self.load_history)
        self.filter_album.textChanged.connect(self.load_history)
        self.filter_status.currentTextChanged.connect(self.load_history)

        # Load initial data
        self.load_history()

        self.setLayout(layout)

    # --------------------------------------------------------
    def load_history(self):
        search = self.search_bar.text()
        artist = self.filter_artist.text()
        album = self.filter_album.text()
        status = self.filter_status.currentText()

        rows = self.history.query(
            search=search,
            artist=artist,
            album=album,
            status=status
        )

        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["flac"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["alac"]))
            self.table.setItem(r, 3, QTableWidgetItem(row["artist"]))
            self.table.setItem(r, 4, QTableWidgetItem(row["album"]))
            self.table.setItem(r, 5, QTableWidgetItem(row["track"]))
            self.table.setItem(r, 6, QTableWidgetItem(str(row["size_before"])))
            self.table.setItem(r, 7, QTableWidgetItem(str(row["size_after"])))
            self.table.setItem(r, 8, QTableWidgetItem(row["date"]))
            self.table.setItem(r, 9, QTableWidgetItem(row["status"]))

    # --------------------------------------------------------
    def open_folder(self, row, column):
        flac_path = self.table.item(row, 1).text()
        folder = os.path.dirname(flac_path)

        if os.name == "nt":
            os.startfile(folder)
        elif os.name == "posix":
            subprocess.Popen(["xdg-open", folder])
        else:
            QMessageBox.information(self, "Open Folder", folder)

    # --------------------------------------------------------
    def export_csv(self):
        out, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not out:
            return

        self.history.export_csv(out)
        QMessageBox.information(self, "Exported", f"History saved to:\n{out}")

    # --------------------------------------------------------
    def clear_history(self):
        if QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to delete ALL conversion history?"
        ) == QMessageBox.StandardButton.Yes:
            self.history.clear_history()
            self.load_history()
