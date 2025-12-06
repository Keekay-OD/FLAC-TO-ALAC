from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from gui.components.folder_selector import FolderSelector
from gui.components.thread_selector import ThreadSelector
from gui.components.progress_item import ProgressItem
from core.converter import ConversionManager


# ============================================================
# Signal Bridge (thread-safe UI update channel)
# ============================================================
class ConvertSignals(QObject):
    progress = pyqtSignal(str, dict)
    complete = pyqtSignal(str, bool, bool)  # path, success, skipped


# ============================================================
# Main Convert Tab Class
# ============================================================
class ConvertTab(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings
        self.history_manager = None       # injected by main_window
        self.manager: ConversionManager = None
        self.progress_items = {}

        # --- Signals ---
        self.signals = ConvertSignals()
        self.signals.progress.connect(self._on_progress_gui)
        self.signals.complete.connect(self._on_complete_gui)

        # --- UI Layout ---
        layout = QVBoxLayout()

        # Folder selector
        self.folder_selector = FolderSelector(settings)
        layout.addWidget(self.folder_selector)

        # Thread selector
        self.thread_selector = ThreadSelector(settings)
        layout.addWidget(self.thread_selector)

        # Buttons
        self.btn_scan = QPushButton("Scan for FLAC Files")
        self.btn_convert = QPushButton("Start Conversion")
        self.btn_convert.setEnabled(False)

        layout.addWidget(self.btn_scan)
        layout.addWidget(self.btn_convert)

        # List of progress widgets
        self.file_list = QListWidget()
        layout.addWidget(self.file_list, 4)

        self.setLayout(layout)

        # Events
        self.btn_scan.clicked.connect(self.scan_files)
        self.btn_convert.clicked.connect(self.start_conversion)

    # ============================================================
    # STEP 1 — SCAN FOR FILES
    # ============================================================
    def scan_files(self):
        folders = self.folder_selector.get_folders()
        if not folders:
            QMessageBox.warning(self, "No Folders", "Please add at least one folder.")
            return

        # Load thread settings
        perf, override = self.thread_selector.get_config()
        self.settings["performance_mode"] = perf
        self.settings["threads_override"] = override

        # Create conversion engine
        self.manager = ConversionManager(
            settings=self.settings,
            history_manager=self.history_manager
        )

        # Scan for flac files
        flac_files = self.manager.scan_for_flac(folders)

        self.file_list.clear()
        self.progress_items.clear()

        for flac in flac_files:
            path_str = str(flac)
            widget = ProgressItem(path_str)
            item = QListWidgetItem(self.file_list)
            item.setSizeHint(widget.sizeHint())
            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, widget)
            self.progress_items[path_str] = widget

        if flac_files:
            self.btn_convert.setEnabled(True)
        else:
            QMessageBox.information(self, "No Files", "No FLAC files found.")

    # ============================================================
    # STEP 2 — START CONVERSION
    # ============================================================
    def start_conversion(self):
        if not self.manager:
            return

        # Tell ConversionManager to emit results via signals
        self.manager.callback_progress = (
            lambda path, info: self.signals.progress.emit(str(path), info)
        )
        self.manager.callback_complete = (
            lambda path, success, skipped=False:
                self.signals.complete.emit(str(path), success, skipped)
        )

        # Queue all conversions
        for path_str, widget in self.progress_items.items():
            widget.update_status("Queued")
            self.manager.convert_file(Path(path_str))

        self.btn_convert.setEnabled(False)

    # ============================================================
    # UI UPDATE — SAFE VIA SIGNALS
    # ============================================================
    def _on_progress_gui(self, flac_path: str, progress: dict):
        """Updates GUI in the main thread only."""
        widget = self.progress_items.get(flac_path)
        if not widget:
            return

        if "out_time_ms" in progress:
            try:
                ms = int(progress["out_time_ms"])
                pct = min(100, ms / 60_000 * 100)  # improved scaling
                widget.progress.setValue(int(pct))
                widget.update_status("Converting")
            except:
                pass

    # ============================================================
    # UI UPDATE — COMPLETION HANDLER
    # ============================================================
    def _on_complete_gui(self, flac_path: str, success: bool, skipped: bool):
        widget = self.progress_items.get(flac_path)
        if not widget:
            return

        if skipped:
            widget.update_status("Skipped")
            widget.progress.setValue(100)
            return

        if success:
            widget.update_status("Done")
            widget.progress.setValue(100)
        else:
            widget.update_status("Failed")
            widget.progress.setValue(0)
