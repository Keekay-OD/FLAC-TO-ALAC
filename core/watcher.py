import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread


class FLACEventHandler(FileSystemEventHandler):

    def __init__(self, callback_new_file):
        self.callback_new_file = callback_new_file

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".flac"):
            self.callback_new_file(Path(event.src_path))

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".flac"):
            self.callback_new_file(Path(event.src_path))


class FolderWatcher:

    def __init__(self, folders, conversion_manager):
        self.folders = folders
        self.manager = conversion_manager
        self.observer = Observer()
        self.running = False

        self.callback_log = None      # UI log messages
        self.callback_file_added = None   # When a file starts converting
        self.callback_done = None     # When converted

    def _log(self, msg):
        if self.callback_log:
            self.callback_log(msg)

    def start(self):
        if self.running:
            return

        self.running = True
        handler = FLACEventHandler(self.on_new_file)

        for folder in self.folders:
            p = Path(folder)
            if p.exists():
                self.observer.schedule(handler, str(p), recursive=True)
                self._log(f"Watching folder: {folder}")

        self.observer.start()
        self._log("Watcher started.")

        # Keep thread alive
        Thread(target=self._watch_loop, daemon=True).start()

    def _watch_loop(self):
        while self.running:
            time.sleep(1)
        self.observer.stop()
        self.observer.join()
        self._log("Watcher stopped.")

    def stop(self):
        self.running = False

    # --------------------------------------------------------
    def on_new_file(self, path: Path):
        """Triggered when watchdog detects a new FLAC file."""
        self._log(f"Detected new FLAC: {path}")

        if self.callback_file_added:
            self.callback_file_added(path)

        # Start conversion
        self.manager.callback_progress = lambda p, d: None  # no GUI progress in watch tab
        self.manager.callback_complete = self.on_conversion_complete
        self.manager.convert_file(path)

    def on_conversion_complete(self, flac_path, success, skipped=False):
        if success:
            msg = f"Converted: {flac_path}"
        elif skipped:
            msg = f"Skipped (already converted): {flac_path}"
        else:
            msg = f"Failed to convert: {flac_path}"

        self._log(msg)

        if self.callback_done:
            self.callback_done(flac_path, success)
