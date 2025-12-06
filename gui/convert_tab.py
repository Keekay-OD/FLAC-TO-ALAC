from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt

from gui.components.folder_selector import FolderSelector
from gui.components.thread_selector import ThreadSelector
from gui.components.progress_item import ProgressItem
from core.converter import ConversionManager
self.history_manager = HistoryManager()


class ConvertTab(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings
        self.history_manager = None   # will be set by main window later
        self.manager = None

        layout = QVBoxLayout()

        # --- Folder selector ---
        self.folder_selector = FolderSelector(settings)
        layout.addWidget(self.folder_selector)

        # --- Thread selector ---
        self.thread_selector = ThreadSelector(settings)
        layout.addWidget(self.thread_selector)

        # --- Buttons ---
        self.btn_scan = QPushButton("Scan for FLAC Files")
        self.btn_convert = QPushButton("Start Conversion")
        self.btn_convert.setEnabled(False)

        layout.addWidget(self.btn_scan)
        layout.addWidget(self.btn_convert)

        # --- Progress area ---
        self.file_list = QListWidget()
        layout.addWidget(self.file_list, 4)

        self.setLayout(layout)

        # Connect signals
        self.btn_scan.clicked.connect(self.scan_files)
        self.btn_convert.clicked.connect(self.start_conversion)

    # ----------------------------------------------------------------------
    def scan_files(self):
        folders = self.folder_selector.get_folders()
        if not folders:
            QMessageBox.warning(self, "No Folders", "Please add at least one folder.")
            return

        # Initialize conversion manager
        perf_mode, override = self.thread_selector.get_config()

        self.manager = ConversionManager(
            settings={
                "performance_mode": perf_mode,
                "threads_override": override,
                "delete_originals": self.settings.get("delete_originals", False)
            },
            history_manager=self.history_manager
        )


        # collect files
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

    # ----------------------------------------------------------------------
    def start_conversion(self):
        if not self.manager:
            return

        # Hook up engine callbacks
        self.manager.callback_progress = self.on_progress_update
        self.manager.callback_complete = self.on_conversion_complete

        # Submit all jobs
        for flac_path in self.progress_items.keys():
            self.progress_items[flac_path].update_status("Queued")
            self.manager.convert_file(Path(flac_path))

        self.btn_convert.setEnabled(False)

    # ----------------------------------------------------------------------
    def on_progress_update(self, flac_path, progress):
        item = self.progress_items[str(flac_path)]

        if "out_time_ms" in progress:
            # Convert ffmpeg time progress to %
            # (This is simplistic; later modules improve accuracy)
            try:
                ms = int(progress["out_time_ms"])
                percent = min(100, ms / 50_000)  # placeholder scaling
                item.progress.setValue(int(percent))
                item.update_status("Converting")
            except:
                pass

    # ----------------------------------------------------------------------
    def on_conversion_complete(self, flac_path, success, skipped=False):
        item = self.progress_items[str(flac_path)]

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
