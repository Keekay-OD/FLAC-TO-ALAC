from pathlib import Path

APP_DIR = Path.home() / ".vibes_flac_alac"
STORAGE_DIR = APP_DIR / "storage"

SETTINGS_FILE = STORAGE_DIR / "settings.json"
HISTORY_DB = STORAGE_DIR / "history.db"
RESUME_FILE = STORAGE_DIR / "resume.json"
LOG_FILE = STORAGE_DIR / "app.log"


def ensure_app_folders():
    APP_DIR.mkdir(exist_ok=True)
    STORAGE_DIR.mkdir(exist_ok=True)
