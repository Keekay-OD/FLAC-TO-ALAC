from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QSpinBox
)


class ThreadSelector(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings

        layout = QHBoxLayout()

        self.mode_label = QLabel("Performance Mode:")
        self.mode_box = QComboBox()
        self.mode_box.addItems(["safe", "balanced", "max", "custom"])

        self.thread_label = QLabel("Threads:")
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 128)
        self.thread_spin.setEnabled(False)

        # Load existing settings
        mode = settings.get("performance_mode", "balanced")
        self.mode_box.setCurrentText(mode)
        if mode == "custom":
            self.thread_spin.setEnabled(True)
            self.thread_spin.setValue(settings.get("threads_override", 4))

        layout.addWidget(self.mode_label)
        layout.addWidget(self.mode_box)
        layout.addWidget(self.thread_label)
        layout.addWidget(self.thread_spin)

        self.setLayout(layout)

        self.mode_box.currentTextChanged.connect(self.on_mode_change)

    def on_mode_change(self, text):
        if text == "custom":
            self.thread_spin.setEnabled(True)
        else:
            self.thread_spin.setEnabled(False)

        self.settings["performance_mode"] = text

    def get_config(self):
        if self.mode_box.currentText() == "custom":
            return ("custom", self.thread_spin.value())
        return (self.mode_box.currentText(), None)
