from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox,
    QComboBox, QSpinBox, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt

from utils.settings_manager import SettingsManager


class SettingsTab(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.manager = SettingsManager()
        self.settings = self.manager.settings  # local reference

        layout = QVBoxLayout()

        # ---------------------------
        # Delete Originals
        # ---------------------------
        self.chk_delete = QCheckBox("Delete original FLAC files after conversion")
        self.chk_delete.setChecked(self.settings.get("delete_originals", False))
        layout.addWidget(self.chk_delete)

        # ---------------------------
        # Performance Mode
        # ---------------------------
        perf_row = QHBoxLayout()
        perf_label = QLabel("Performance Mode:")
        self.combo_perf = QComboBox()
        self.combo_perf.addItems(["safe", "balanced", "max", "custom"])

        current_perf = self.settings.get("performance_mode", "balanced")
        self.combo_perf.setCurrentText(current_perf)

        perf_row.addWidget(perf_label)
        perf_row.addWidget(self.combo_perf)
        layout.addLayout(perf_row)

        # ---------------------------
        # Custom Thread Count
        # ---------------------------
        threads_row = QHBoxLayout()
        threads_label = QLabel("Custom Thread Count:")
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 128)
        self.spin_threads.setEnabled(current_perf == "custom")

        override = self.settings.get("threads_override")
        if override:
            self.spin_threads.setValue(int(override))

        threads_row.addWidget(threads_label)
        threads_row.addWidget(self.spin_threads)
        layout.addLayout(threads_row)

        # Change enable state when performance mode switches
        self.combo_perf.currentTextChanged.connect(
            lambda x: self.spin_threads.setEnabled(x == "custom")
        )

        # ---------------------------
        # Save + Reset Buttons
        # ---------------------------
        btn_save = QPushButton("Save Settings")
        btn_reset = QPushButton("Restore Defaults")

        layout.addWidget(btn_save)
        layout.addWidget(btn_reset)

        btn_save.clicked.connect(self.save_settings)
        btn_reset.clicked.connect(self.reset_settings)

        layout.addStretch()
        self.setLayout(layout)

    # ---------------------------------------------------------------------
    def save_settings(self):
        """Save settings to disk."""
        self.settings["delete_originals"] = self.chk_delete.isChecked()
        self.settings["performance_mode"] = self.combo_perf.currentText()

        if self.combo_perf.currentText() == "custom":
            self.settings["threads_override"] = self.spin_threads.value()
        else:
            self.settings["threads_override"] = None

        self.manager.save()

        QMessageBox.information(self, "Settings Saved", "Settings have been updated.")

    # ---------------------------------------------------------------------
    def reset_settings(self):
        """Restore default settings."""
        if QMessageBox.question(
            self, "Reset Settings", "Restore default settings?"
        ) != QMessageBox.StandardButton.Yes:
            return

        default = self.manager.default_settings()
        self.manager.save(default)
        self.settings = default

        # Refresh UI
        self.chk_delete.setChecked(False)
        self.combo_perf.setCurrentText("balanced")
        self.spin_threads.setValue(4)
        self.spin_threads.setEnabled(False)

        QMessageBox.information(self, "Reset", "Default settings restored.")
