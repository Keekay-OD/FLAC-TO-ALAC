from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class SettingsTab(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings

        layout = QVBoxLayout()

        label = QLabel("Application Settings\n\n(All settings implemented in Module 8)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)

        self.setLayout(layout)
