from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QProgressBar, QFrame
)
from PyQt6.QtCore import Qt


class ProgressItem(QWidget):

    def __init__(self, file_path: str):
        super().__init__()

        self.file_path = file_path
        self.status = "Queued"   # <—— REAL STATUS ATTRIBUTE HERE

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

        # top row
        top = QHBoxLayout()

        self.lbl_name = QLabel(file_path)
        self.lbl_name.setStyleSheet("font-weight: bold; color: white;")

        self.lbl_status = QLabel(self.status)
        self.lbl_status.setStyleSheet("color: #959ba0; font-weight: bold;")

        top.addWidget(self.lbl_name)
        top.addStretch()
        top.addWidget(self.lbl_status)

        # progress
        self.progress = QProgressBar()
        self.progress.setValue(0)

        # divider
        line = QFrame()
        line.setObjectName("line")
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)

        root.addLayout(top)
        root.addWidget(self.progress)
        root.addWidget(line)

        self.setLayout(root)

    # ---------------------------------------------
    # UPDATE STATUS + STORE TO .status
    # ---------------------------------------------
    def update_status(self, status: str):

        self.status = status   # <—— THIS WAS MISSING

        colors = {
            "Queued": "#959ba0",
            "Converting": "#5865F2",
            "Done": "#57F287",
            "Failed": "#ED4245",
            "Skipped": "#FEE75C",
        }

        color = colors.get(status, "white")

        self.lbl_status.setText(status)
        self.lbl_status.setStyleSheet(
            f"color: {color}; font-weight: bold;"
        )
