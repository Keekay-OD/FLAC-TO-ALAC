from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

from gui.components.folder_selector import FolderSelector
from gui.components.thread_selector import ThreadSelector
from gui.components.progress_item import ProgressItem
from core.converter import ConversionManager


# --------------------------------------------
# Thread-safe signals
# --------------------------------------------
class ProgressSignal(QObject):
    progress = pyqtSignal(object, float)
    complete = pyqtSignal(object, bool, bool)


class ConvertTab(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings
        self.history_manager = None     # injected by main window
        self.manager = None
        self.progress_items = {}
        self.pending = []               # queue of files

        # --------------------------------------------
        # STYLES
        # --------------------------------------------
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2d31;
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #5865F2;
                color: white;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:disabled {
                background-color: #42464d;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
            QListWidget {
                background-color: #313338;
                border: 1px solid #1e1f22;
            }
        """)

        # --------------------------------------------
        # LAYOUT
        # --------------------------------------------
        layout = QVBoxLayout()

        self.folder_selector = FolderSelector(settings)
        layout.addWidget(self.folder_selector)

        self.thread_selector = ThreadSelector(settings)
        layout.addWidget(self.thread_selector)

        self.btn_scan = QPushButton("Scan for FLAC Files")
        self.btn_convert = QPushButton("Start Conversion")
        self.btn_convert.setEnabled(False)

        layout.addWidget(self.btn_scan)
        layout.addWidget(self.btn_convert)

        self.file_list = QListWidget()
        layout.addWidget(self.file_list, 4)

        self.setLayout(layout)

        # --------------------------------------------
        # SIGNALS
        # --------------------------------------------
        self.btn_scan.clicked.connect(self.scan_files)
        self.btn_convert.clicked.connect(self.start_conversion)

        self.signals = ProgressSignal()
        self.signals.progress.connect(self.update_progress_ui)
        self.signals.complete.connect(self.update_complete_ui)

    # ======================================================================
    # SCAN
    # ======================================================================
    def scan_files(self):
        folders = self.folder_selector.get_folders()

        if not folders:
            QMessageBox.warning(self, "No Folders", "Please add at least one folder.")
            return

        self.settings["last_folders"] = folders

        perf_mode, override = self.thread_selector.get_config()
        self.settings["performance_mode"] = perf_mode
        self.settings["threads_override"] = override

        self.manager = ConversionManager(
            settings=self.settings,
            history_manager=self.history_manager
        )

        flac_files = self.manager.scan_for_flac(folders)

        self.file_list.clear()
        self.progress_items = {}
        self.pending = []

        for f in flac_files:
            row = ProgressItem(str(f))
            item = QListWidgetItem(self.file_list)
            item.setSizeHint(row.sizeHint())

            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, row)

            self.progress_items[str(f)] = row
            self.pending.append(str(f))

        if flac_files:
            self.btn_convert.setEnabled(True)
        else:
            QMessageBox.information(self, "No Files", "No FLAC files found.")

    # ======================================================================
    # START CONVERSION
    # ======================================================================
    def start_conversion(self):
        if not self.manager:
            return

        self.manager.callback_progress = self.forward_progress
        self.manager.callback_complete = self.forward_complete

        # mark all Queued
        for p in self.pending:
            self.progress_items[p].update_status("Queued")

        self.btn_convert.setEnabled(False)
        self.start_next_batch()

    # ======================================================================
    # BATCH PROCESSOR (the new magic)
    # ======================================================================
    def start_next_batch(self):
        if not self.pending:
            # all files done
            self.scan_files()  # auto-refresh
            return

        running = sum(
            1 for p in self.progress_items.values()
            if p.status == "Converting"
        )



        limit = self.manager.thread_pool.max_workers

        if running >= limit:
            return

        next_path = self.pending.pop(0)
        row = self.progress_items[next_path]
        row.update_status("Converting")

        self.manager.convert_file(Path(next_path))

    # ======================================================================
    # SIGNAL FORWARD
    # ======================================================================
    def forward_progress(self, flac_path, pct):
        self.signals.progress.emit(str(flac_path), pct)

    def forward_complete(self, flac_path, success, skipped=False):
        self.signals.complete.emit(str(flac_path), success, skipped)

    # ======================================================================
    # UI UPDATES
    # ======================================================================
    def update_progress_ui(self, flac_path, pct):
        item = self.progress_items.get(str(flac_path))
        if not item:
            return
        item.progress.setValue(int(pct))
        item.update_status("Converting")

    def update_complete_ui(self, flac_path, success, skipped=False):
        item = self.progress_items.get(str(flac_path))
        if not item:
            return

        if skipped:
            item.update_status("Skipped")
            item.progress.setValue(100)
        elif success:
            item.update_status("Done")
            item.progress.setValue(100)
        else:
            item.update_status("Failed")
            item.progress.setValue(0)

        # Start the next file
        self.start_next_batch()
