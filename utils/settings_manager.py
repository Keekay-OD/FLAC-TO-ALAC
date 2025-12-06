import json
from utils.paths import SETTINGS_FILE


class SettingsManager:

    def __init__(self):
        self.settings = self.load()

    # ---------------------
    def load(self):
        if not SETTINGS_FILE.exists():
            default = self.default_settings()
            self.save(default)
            return default

        try:
            return json.loads(SETTINGS_FILE.read_text())
        except:
            default = self.default_settings()
            self.save(default)
            return default

    # ---------------------
    def save(self, settings=None):
        if settings is not None:
            self.settings = settings

        SETTINGS_FILE.write_text(json.dumps(self.settings, indent=4))

    # ---------------------
    @staticmethod
    def default_settings():
        return {
            "delete_originals": False,
            "performance_mode": "balanced",
            "threads_override": None,
            "watched_folders": [],
            "dark_mode": True
        }
