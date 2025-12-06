from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox,
    QComboBox, QSpinBox, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
import json

from utils.paths import SETTINGS_FILE


class SettingsTab(QWidget):

    def __init__(self, settings: dict):
        super().__init__()

        # Shared global settings dictionary passed from MainWindow
        self.settings = settings

        layout = QVBoxLayout()

        # ----------------------------------------------------------
        # Delete Originals
        # ----------------------------------------------------------
        self.chk_delete = QCheckBox("Delete original FLAC files after conversion")
        self.chk_delete.setChecked(self.settings.get("delete_originals", False))
        layout.addWidget(self.chk_delete)

        # ----------------------------------------------------------
        # Performance Mode
        # ----------------------------------------------------------
        perf_row = QHBoxLayout()
        perf_label = QLabel("Performance Mode:")
        self.combo_perf = QComboBox()
        self.combo_perf.addItems(["safe", "balanced", "max", "custom"])

        current_perf = self.settings.get("performance_mode", "balanced")
        self.combo_perf.setCurrentText(current_perf)

        perf_row.addWidget(perf_label)
        perf_row.addWidget(self.combo_perf)
        layout.addLayout(perf_row)

        # ----------------------------------------------------------
        # Custom Thread Count
        # ----------------------------------------------------------
        threads_row = QHBoxLayout()
        threads_label = QLabel("Custom Thread Count:")
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 128)

        override = self.settings.get("threads_override")
        if override:
            self.spin_threads.setValue(int(override))

        self.spin_threads.setEnabled(current_perf == "custom")

        threads_row.addWidget(threads_label)
        threads_row.addWidget(self.spin_threads)
        layout.addLayout(threads_row)

        # Enable only when "custom" is selected
        self.combo_perf.currentTextChanged.connect(
            lambda mode: self.spin_threads.setEnabled(mode == "custom")
        )

        # ----------------------------------------------------------
        # Save + Reset
        # ----------------------------------------------------------
        btn_save = QPushButton("Save Settings")
        btn_reset = QPushButton("Restore Defaults")
        layout.addWidget(btn_save)
        layout.addWidget(btn_reset)

        btn_save.clicked.connect(self.save_settings)
        btn_reset.clicked.connect(self.reset_settings)

        layout.addStretch()
        self.setLayout(layout)

    # ==============================================================
    # SAVE SETTINGS
    # ==============================================================
    def save_settings(self):
        # Update settings dict from UI
        self.settings["delete_originals"] = self.chk_delete.isChecked()
        self.settings["performance_mode"] = self.combo_perf.currentText()

        if self.combo_perf.currentText() == "custom":
            self.settings["threads_override"] = self.spin_threads.value()
        else:
            self.settings["threads_override"] = None

        # Write to disk
        SETTINGS_FILE.write_text(json.dumps(self.settings, indent=4))

        QMessageBox.information(self, "Settings Saved", "Settings have been updated.")
        print("Settings updated ->", self.settings)

    # ==============================================================
    # RESET SETTINGS
    # ==============================================================
    def reset_settings(self):

        if QMessageBox.question(
            self, "Reset Settings", "Restore default settings?"
        ) != QMessageBox.StandardButton.Yes:
            return

        # Defaults
        self.settings["delete_originals"] = False
        self.settings["performance_mode"] = "balanced"
        self.settings["threads_override"] = None

        # Update UI
        self.chk_delete.setChecked(False)
        self.combo_perf.setCurrentText("balanced")
        self.spin_threads.setValue(4)
        self.spin_threads.setEnabled(False)

        QMessageBox.information(self, "Reset", "Default settings restored.")
