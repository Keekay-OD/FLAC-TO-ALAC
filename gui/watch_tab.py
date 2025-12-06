from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class WatchTab(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings

        layout = QVBoxLayout()

        label = QLabel("Real-time FLAC Watching\n\n(Watcher engine added in Module 7)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        self.setLayout(layout)
