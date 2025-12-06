from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt


class ConvertTab(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings

        layout = QVBoxLayout()
        label = QLabel("Convert FLAC → ALAC\n\n(Features will be added in Module 3)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        self.setLayout(layout)
