from pathlib import Path
import sys
import json


# ------------------------------------------------------------
# Detect source vs. PyInstaller EXE
# ------------------------------------------------------------
def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()


# ------------------------------------------------------------
# /appdata folder for DB + settings + resume
# ------------------------------------------------------------
APP_DATA_DIR = BASE_DIR / "appdata"


def ensure_app_folders():
    """Ensure required folders and files exist."""
    APP_DATA_DIR.mkdir(exist_ok=True)

    # Create empty defaults if missing
    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.write_text(json.dumps({
            "delete_originals": False,
            "performance_mode": "balanced",
            "threads_override": None
        }, indent=4))

    if not RESUME_FILE.exists():
        RESUME_FILE.write_text(json.dumps({"converted": []}, indent=4))

    # Create empty SQLite DB if missing (tables created later)
    if not HISTORY_DB.exists():
        HISTORY_DB.touch()


# ------------------------------------------------------------
# Settings file
# ------------------------------------------------------------
SETTINGS_FILE = APP_DATA_DIR / "settings.json"


# ------------------------------------------------------------
# Resume file
# ------------------------------------------------------------
RESUME_FILE = APP_DATA_DIR / "resume.json"


# ------------------------------------------------------------
# SQLite history DB
# ------------------------------------------------------------
HISTORY_DB = APP_DATA_DIR / "history.db"


# Ensure structure exists on import
ensure_app_folders()
