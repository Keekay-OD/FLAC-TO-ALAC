from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSpinBox
)
from PyQt6.QtCore import Qt


class ThreadSelector(QWidget):

    def __init__(self, settings: dict):
        super().__init__()

        self.settings = settings

        self.performance_mode = settings.get("performance_mode", "balanced")
        self.override_value = settings.get("threads_override", None)

        # -----------------------------------------------
        # Discord-themed styling
        # -----------------------------------------------
        self.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
            }

            QPushButton {
                background-color: #313338;
                color: white;
                border: 1px solid #1e1f22;
                border-radius: 16px;
                padding: 6px 14px;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: #3c3f45;
            }

            QPushButton[selected="true"] {
                background-color: #5865F2;
                border: 1px solid #4752C4;
                color: white;
                font-weight: bold;
            }

            QSpinBox {
                background-color: #313338;
                color: white;
                border: 1px solid #1e1f22;
                padding: 4px;
                border-radius: 6px;
                width: 80px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Performance Mode")
        title.setStyleSheet("font-weight: bold; font-size: 15px; margin-bottom: 4px;")
        layout.addWidget(title)

        # ----------------------------------------------------------
        # PILLS (safe • balanced • max • custom)
        # ----------------------------------------------------------
        pill_row = QHBoxLayout()
        pill_row.setSpacing(10)

        self.btn_safe = QPushButton("Safe")
        self.btn_balanced = QPushButton("Balanced")
        self.btn_max = QPushButton("Max")
        self.btn_custom = QPushButton("Custom")

        self.pills = [
            ("safe", self.btn_safe),
            ("balanced", self.btn_balanced),
            ("max", self.btn_max),
            ("custom", self.btn_custom),
        ]

        for mode, btn in self.pills:
            btn.clicked.connect(lambda _, m=mode: self.select_mode(m))
            pill_row.addWidget(btn)

        layout.addLayout(pill_row)

        # ----------------------------------------------------------
        # CUSTOM THREAD SPINBOX
        # ----------------------------------------------------------
        self.custom_row = QHBoxLayout()
        lbl_custom = QLabel("Custom Thread Count:")
        lbl_custom.setFixedWidth(160)

        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 128)
        self.spin_threads.setValue(self.override_value if self.override_value else 4)

        self.custom_row.addWidget(lbl_custom)
        self.custom_row.addWidget(self.spin_threads)

        layout.addLayout(self.custom_row)

        self.custom_row.setContentsMargins(10, 0, 0, 0)

        self.setLayout(layout)

        # Apply initial mode selection
        self.select_mode(self.performance_mode)

    # ===================================================================
    # Handle pill selection
    # ===================================================================
    def select_mode(self, mode: str):
        self.performance_mode = mode

        # Update UI states
        for m, btn in self.pills:
            btn.setProperty("selected", "true" if m == mode else "false")
            btn.setStyle(btn.style())  # refresh

        # Enable/disable custom thread spinner
        if mode == "custom":
            self.spin_threads.setEnabled(True)
        else:
            self.spin_threads.setEnabled(False)

    # ===================================================================
    # ConvertTab will call this to read the settings
    # ===================================================================
    def get_config(self):
        if self.performance_mode == "custom":
            return "custom", self.spin_threads.value()

        return self.performance_mode, None
