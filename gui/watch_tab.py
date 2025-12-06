from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QMessageBox
)
from PyQt6.QtCore import Qt

from gui.components.folder_selector import FolderSelector
from core.converter import ConversionManager
from core.watcher import FolderWatcher
from core.history_manager import HistoryManager


class WatchTab(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings
        self.watcher = None
        self.converter = None
        self.history = HistoryManager()

        layout = QVBoxLayout()

        # -----------------------
        # Folder Selector
        # -----------------------
        self.folder_selector = FolderSelector(settings)
        layout.addWidget(self.folder_selector)

        # -----------------------
        # Start/Stop Buttons
        # -----------------------
        self.btn_start = QPushButton("Start Watching")
        self.btn_stop = QPushButton("Stop Watching")
        self.btn_stop.setEnabled(False)

        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)

        # -----------------------
        # Status Label
        # -----------------------
        self.label_status = QLabel("Status: Not Running")
        layout.addWidget(self.label_status)

        # -----------------------
        # Event Log
        # -----------------------
        self.log_list = QListWidget()
        layout.addWidget(self.log_list, 3)

        # Events
        self.btn_start.clicked.connect(self.start_watch)
        self.btn_stop.clicked.connect(self.stop_watch)

        self.setLayout(layout)

    # ---------------------------------------------------------
    def log(self, msg):
        self.log_list.addItem(msg)
        self.log_list.scrollToBottom()

    # ---------------------------------------------------------
    def start_watch(self):
        folders = self.folder_selector.get_folders()
        if not folders:
            QMessageBox.warning(self, "No Folders", "Add at least one folder to watch.")
            return

        # Build converter with settings
        perf = self.settings.get("performance_mode", "balanced")
        override = self.settings.get("threads_override")

        self.converter = ConversionManager(
            settings=self.settings,
            history_manager=self.history
        )

        # Build watcher
        self.watcher = FolderWatcher(folders, self.converter)
        self.watcher.callback_log = self.log
        self.watcher.callback_file_added = lambda p: self.log(f"Converting: {p}")
        self.watcher.callback_done = lambda p, s: self.log(
            f"Converted: {p}" if s else f"Failed: {p}"
        )

        self.watcher.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.label_status.setText("Status: Running")

    # ---------------------------------------------------------
    def stop_watch(self):
        if self.watcher:
            self.watcher.stop()
            self.watcher = None

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.label_status.setText("Status: Not Running")

        self.log("Watcher stopped.")
