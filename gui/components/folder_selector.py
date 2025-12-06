from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QFrame
)
from PyQt6.QtCore import Qt
import os


class FolderCard(QWidget):
    """A Discord-style card representing a single folder."""

    def __init__(self, folder_path: str, remove_callback):
        super().__init__()

        self.folder = folder_path
        self.remove_callback = remove_callback

        self.setStyleSheet("""
            QWidget {
                background-color: #313338;
                border: 1px solid #1e1f22;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
            QPushButton {
                background-color: #ED4245;
                color: white;
                padding: 4px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c03532;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.lbl = QLabel(folder_path)
        self.lbl.setWordWrap(False)

        btn_remove = QPushButton("✕")
        btn_remove.setFixedWidth(30)
        btn_remove.clicked.connect(lambda: self.remove_callback(self.folder))

        layout.addWidget(self.lbl)
        layout.addStretch()
        layout.addWidget(btn_remove)

        self.setLayout(layout)


class FolderSelector(QWidget):

    def __init__(self, settings: dict):
        super().__init__()

        self.settings = settings
        self.folder_list = settings.get("folders", [])

        self.setStyleSheet("""
            QPushButton {
                background-color: #5865F2;
                color: white;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
        """)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)

        # Title
        title = QLabel("Selected Music Folders")
        title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: bold; margin-bottom: 4px;")
        self.layout.addWidget(title)

        # Folder cards container
        self.card_container = QVBoxLayout()
        self.card_container.setSpacing(8)
        self.layout.addLayout(self.card_container)

        # "Add folder" button
        btn_add = QPushButton("Add Folder")
        btn_add.clicked.connect(self.add_folder_dialog)
        self.layout.addWidget(btn_add)

        self.layout.addStretch()
        self.setLayout(self.layout)

        # Load saved folders
        self.refresh_cards()

    # ----------------------------------------------------------
    # Refresh folder cards
    # ----------------------------------------------------------
    def refresh_cards(self):
        while self.card_container.count() > 0:
            item = self.card_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for folder in self.folder_list:
            card = FolderCard(folder, self.remove_folder)
            self.card_container.addWidget(card)

    # ----------------------------------------------------------
    # Add Folder
    # ----------------------------------------------------------
    def add_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")

        if not folder:
            return

        folder = os.path.normpath(folder)

        if folder not in self.folder_list:
            self.folder_list.append(folder)
            self.settings["folders"] = self.folder_list
            self.refresh_cards()

    # ----------------------------------------------------------
    # Remove Folder
    # ----------------------------------------------------------
    def remove_folder(self, folder):
        if folder in self.folder_list:
            self.folder_list.remove(folder)
            self.settings["folders"] = self.folder_list
            self.refresh_cards()

    # ----------------------------------------------------------
    # Called by ConvertTab
    # ----------------------------------------------------------
    def get_folders(self) -> list:
        return list(self.folder_list)
