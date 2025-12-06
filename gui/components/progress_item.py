from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt


class ProgressItem(QWidget):

    def __init__(self, flac_path: str):
        super().__init__()

        self.flac_path = flac_path

        layout = QHBoxLayout()

        self.label_name = QLabel(flac_path)
        self.label_status = QLabel("Pending")
        self.progress = QProgressBar()
        self.progress.setValue(0)

        layout.addWidget(self.label_name, 3)
        layout.addWidget(self.label_status, 1)
        layout.addWidget(self.progress, 2)

        self.setLayout(layout)

    def update_status(self, text):
        self.label_status.setText(text)

    def update_progress(self, percent):
        self.progress.setValue(percent)
