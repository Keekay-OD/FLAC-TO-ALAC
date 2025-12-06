from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QHBoxLayout
)


class FolderSelector(QWidget):

    def __init__(self, settings):
        super().__init__()

        self.settings = settings

        layout = QVBoxLayout()
        btn_row = QHBoxLayout()

        self.btn_add = QPushButton("Add Folder")
        self.btn_remove = QPushButton("Remove Selected")

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_remove)

        self.folder_list = QListWidget()
        for f in settings.get("watched_folders", []):
            self.folder_list.addItem(f)

        layout.addLayout(btn_row)
        layout.addWidget(self.folder_list)
        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_folder)
        self.btn_remove.clicked.connect(self.remove_selected)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder:
            self.folder_list.addItem(folder)
            self.save()

    def remove_selected(self):
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))
        self.save()

    def get_folders(self):
        return [self.folder_list.item(i).text()
                for i in range(self.folder_list.count())]

    def save(self):
        self.settings["watched_folders"] = self.get_folders()
