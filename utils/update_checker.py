import json
import urllib.request
from PyQt6.QtWidgets import QMessageBox
import webbrowser
from utils.version import APP_VERSION

UPDATE_URL = "https://raw.githubusercontent.com/Keekay-OD/FLAC-TO-ALAC/main/latest.json"

def check_for_updates(parent=None):
    try:
        with urllib.request.urlopen(UPDATE_URL, timeout=5) as r:
            data = json.loads(r.read().decode())
    except:
        return

    latest = data.get("latest_version")
    dl = data.get("download_url")
    notes = data.get("release_notes", "")

    if not latest or not dl:
        return

    if latest.strip() == APP_VERSION.strip():
        return

    msg = QMessageBox(parent)
    msg.setWindowTitle("Update Available")
    msg.setText(
        f"A new version of VibesFLAC is available!\n\n"
        f"Your version: {APP_VERSION}\n"
        f"Latest version: {latest}\n\n"
        f"{notes}"
    )
    msg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    msg.button(QMessageBox.StandardButton.Yes).setText("Download")
    msg.button(QMessageBox.StandardButton.No).setText("Later")

    if msg.exec() == QMessageBox.StandardButton.Yes:
        webbrowser.open(dl)
