from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from gui.convert_tab import ConvertTab
from gui.history_tab import HistoryTab
from gui.watch_tab import WatchTab
from gui.settings_tab import SettingsTab

from core.history_manager import HistoryManager

APP_TITLE = "Vibes FLAC → ALAC Converter"


class MainWindow(QMainWindow):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings

        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1100, 700)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)

        # Tab container
        self.tabs = QTabWidget()
        self.tabs.setMovable(False)
        self.tabs.setTabsClosable(False)

        # Shared history database
        self.history = HistoryManager()

        # --------------------------------------------------------
        # Create tabs
        # --------------------------------------------------------
        self.convert_tab = ConvertTab(self.settings)
        self.history_tab = HistoryTab()
        self.watch_tab = WatchTab(self.settings)
        self.settings_tab = SettingsTab(self.settings)

        # Inject shared history AFTER creating tabs
        self.convert_tab.history_manager = self.history
        self.watch_tab.history = self.history

        # SettingsTab needs access to convert tab's settings
        self.settings_tab.manager = self.convert_tab.settings

        # --------------------------------------------------------
        # Add tabs to the UI
        # --------------------------------------------------------
        self.tabs.addTab(self.convert_tab, "Convert")
        self.tabs.addTab(self.history_tab, "History")
        self.tabs.addTab(self.watch_tab, "Watch")
        self.tabs.addTab(self.settings_tab, "Settings")

        # Root layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        container.setLayout(layout)
        self.setCentralWidget(container)
