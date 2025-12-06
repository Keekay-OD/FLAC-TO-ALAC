from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class HistoryTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        label = QLabel("History of Conversions\n\n(Search + filters will appear in Module 5)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        self.setLayout(layout)
