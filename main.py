import sys
import json
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from gui.main_window import MainWindow
from utils.paths import ensure_app_folders, SETTINGS_FILE


APP_NAME = "Vibes FLAC → ALAC Converter"
APP_VERSION = "1.0.0"


DEFAULT_SETTINGS = {
    "delete_originals": False,
    "performance_mode": "balanced",
    "threads_override": None,
    "watched_folders": [],
    "dark_mode": True
}


def load_settings():
    """Load settings file or restore defaults if corrupted."""
    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.write_text(json.dumps(DEFAULT_SETTINGS, indent=4))
        return DEFAULT_SETTINGS.copy()

    try:
        data = json.loads(SETTINGS_FILE.read_text())

        # Ensure missing keys get default values
        for k, v in DEFAULT_SETTINGS.items():
            if k not in data:
                data[k] = v

        return data

    except Exception:
        # Auto-repair damaged settings file
        SETTINGS_FILE.write_text(json.dumps(DEFAULT_SETTINGS, indent=4))
        return DEFAULT_SETTINGS.copy()


def apply_dark_theme(app: QApplication):
    """Apply a modern dark mode theme."""
    DARK_STYLE = """
    QWidget {
        background-color: #1E1E1E;
        color: #DDDDDD;
        font-size: 14px;
    }

    QLineEdit, QTextEdit, QListWidget, QTreeWidget, QTableWidget {
        background-color: #2B2B2B;
        border: 1px solid #444;
        padding: 4px;
    }

    QPushButton {
        background-color: #333;
        border: 1px solid #555;
        padding: 6px 12px;
        border-radius: 4px;
    }

    QPushButton:hover {
        background-color: #444;
    }

    QPushButton:pressed {
        background-color: #555;
    }

    QTabWidget::pane {
        border: 1px solid #444;
        background-color: #1E1E1E;
    }

    QTabBar::tab {
        background: #2A2A2A;
        padding: 8px;
        border: 1px solid #444;
        border-bottom: 0px;
    }

    QTabBar::tab:selected {
        background: #444;
    }
    """

    app.setStyleSheet(DARK_STYLE)


def main():
    """Main application startup."""
    ensure_app_folders()  # MUST run first

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    apply_dark_theme(app)

    settings = load_settings()

    window = MainWindow(settings)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
