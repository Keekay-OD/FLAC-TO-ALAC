from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QProgressBar, QFrame
)
from PyQt6.QtCore import Qt


class ProgressItem(QWidget):

    def __init__(self, file_path: str):
        super().__init__()

        self.file_path = file_path

        self.setStyleSheet("""
            QWidget {
                background-color: #313338;
                color: white;
                font-size: 13px;
            }
            QFrame#line {
                background-color: #1e1f22;
            }
            QLabel {
                color: white;
            }
            QProgressBar {
                background-color: #1e1f22;
                border: 1px solid #1e1f22;
                border-radius: 6px;
                height: 14px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #5865F2;
                border-radius: 6px;
            }
        """)

        root = QVBoxLayout()
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(4)

        # -------------------------------
        # Top Row: Filename + Status
        # -------------------------------
        top_row = QHBoxLayout()

        self.lbl_name = QLabel(file_path)
        self.lbl_name.setStyleSheet("font-weight: bold; color: white;")

        self.lbl_status = QLabel("Queued")
        self.lbl_status.setStyleSheet("color: #959ba0;")

        top_row.addWidget(self.lbl_name)
        top_row.addStretch()
        top_row.addWidget(self.lbl_status)

        # -------------------------------
        # Progress Bar
        # -------------------------------
        self.progress = QProgressBar()
        self.progress.setValue(0)

        # Divider line
        line = QFrame()
        line.setObjectName("line")
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)

        # Layout assembly
        root.addLayout(top_row)
        root.addWidget(self.progress)
        root.addWidget(line)

        self.setLayout(root)

    # ------------------------------------------------------
    # Update Status Label (Discord styling)
    # ------------------------------------------------------
    def update_status(self, status: str):

        colors = {
            "Queued": "#959ba0",
            "Converting": "#5865F2",
            "Done": "#57F287",
            "Failed": "#ED4245",
            "Skipped": "#FEE75C",
        }

        color = colors.get(status, "white")

        self.lbl_status.setText(status)
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold;")
