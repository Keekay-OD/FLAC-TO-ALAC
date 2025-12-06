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


# --------------------------------------------------------------
# Thread-safe signal bridge (Qt requires UI changes on main thread)
# --------------------------------------------------------------
class ProgressSignal(QObject):
    progress = pyqtSignal(object, float)
    complete = pyqtSignal(object, bool, bool)


class ConvertTab(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings
        self.history_manager = None
        self.manager = None
        self.progress_items = {}

        # ----------------------------------------------------------
        # Discord-style background
        # ----------------------------------------------------------
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

        # ----------------------------------------------------------
        # UI LAYOUT
        # ----------------------------------------------------------
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

        # SIGNALS
        self.btn_scan.clicked.connect(self.scan_files)
        self.btn_convert.clicked.connect(self.start_conversion)

        # Thread-safe signal forwarding
        self.signals = ProgressSignal()
        self.signals.progress.connect(self.update_progress_ui)
        self.signals.complete.connect(self.update_complete_ui)

    # ==============================================================================
    # SCAN
    # ==============================================================================
    def scan_files(self):
        folders = self.folder_selector.get_folders()

        if not folders:
            QMessageBox.warning(self, "No Folders", "Please add at least one folder.")
            return

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

        for f in flac_files:
            item_widget = ProgressItem(str(f))
            item = QListWidgetItem(self.file_list)
            item.setSizeHint(item_widget.sizeHint())

            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, item_widget)

            self.progress_items[str(f)] = item_widget

        if flac_files:
            self.btn_convert.setEnabled(True)
        else:
            QMessageBox.information(self, "No Files", "No FLAC files found.")

    # ==============================================================================
    # START CONVERSION
    # ==============================================================================
    def start_conversion(self):
        if not self.manager:
            return

        self.manager.callback_progress = self.forward_progress
        self.manager.callback_complete = self.forward_complete

        for flac_path in self.progress_items.keys():
            self.progress_items[flac_path].update_status("Queued")
            self.manager.convert_file(Path(flac_path))

        self.btn_convert.setEnabled(False)

    # ==============================================================================
    # CALLBACK FORWARDING (thread → Qt)
    # ==============================================================================
    def forward_progress(self, flac_path, pct):
        self.signals.progress.emit(flac_path, pct)

    def forward_complete(self, flac_path, success, skipped=False):
        self.signals.complete.emit(flac_path, success, skipped)

    # ==============================================================================
    # UI UPDATES (Qt thread)
    # ==============================================================================
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
            return

        if success:
            item.update_status("Done")
            item.progress.setValue(100)
        else:
            item.update_status("Failed")
            item.progress.setValue(0)

        # REMOVE ITEM FROM QUEUE AFTER DONE
        # (optional but matches your old behavior)
