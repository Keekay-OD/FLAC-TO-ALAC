import subprocess
from pathlib import Path
from datetime import datetime
import json

from core.ffmpeg_progress import FFmpegProgress
from core.metadata import extract_flac_metadata, write_alac_metadata
from core.threads import ConversionThreadPool
from utils.paths import RESUME_FILE


class ConversionManager:

    def __init__(self, settings, history_manager):
        self.settings = settings
        self.history = history_manager

        self.resume_state = self.load_resume_state()
        self.thread_pool = ConversionThreadPool(
            performance_mode=settings.get("performance_mode", "balanced"),
            override=settings.get("threads_override")
        )

        self.callback_progress = None     # (path, progress_dict)
        self.callback_complete = None     # (path, success)

    # ----------------------------------------------------------------------
    # Resume State Management
    # ----------------------------------------------------------------------
    def load_resume_state(self):
        if not RESUME_FILE.exists():
            return {"converted": []}

        try:
            return json.loads(RESUME_FILE.read_text())
        except:
            return {"converted": []}

    def save_resume_state(self):
        RESUME_FILE.write_text(json.dumps(self.resume_state, indent=4))

    def mark_converted(self, path: Path):
        path_str = str(path)
        if path_str not in self.resume_state["converted"]:
            self.resume_state["converted"].append(path_str)
            self.save_resume_state()

    def already_converted(self, path: Path):
        return str(path) in self.resume_state["converted"]

    # ----------------------------------------------------------------------
    # Queue a conversion job
    # ----------------------------------------------------------------------
    def convert_file(self, flac_path: Path):
        """Submit file to thread pool."""
        return self.thread_pool.submit(self._convert_worker, flac_path)

    # ----------------------------------------------------------------------
    # The worker that performs the conversion
    # ----------------------------------------------------------------------
    def _convert_worker(self, flac_path: Path):
        m4a_path = flac_path.with_suffix(".m4a")

        if self.already_converted(flac_path):
            if self.callback_complete:
                self.callback_complete(flac_path, True, skipped=True)
            return

        metadata, cover = extract_flac_metadata(flac_path)

        # FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", str(flac_path),
            "-c:a", "alac",
            "-progress", "pipe:1",
            "-nostats",
            "-y",
            str(m4a_path)
        ]

        # Progress handler
        def on_update(info):
            if self.callback_progress:
                self.callback_progress(flac_path, info)

        # Completion handler
        def on_complete(success):
            if success:
                write_alac_metadata(m4a_path, metadata, cover)
                self.history.add_record(
                    flac=str(flac_path),
                    alac=str(m4a_path),
                    metadata=metadata,
                    size_before=flac_path.stat().st_size,
                    size_after=m4a_path.stat().st_size
                )

                if self.settings.get("delete_originals", False):
                    try:
                        flac_path.unlink()
                    except:
                        pass

                self.mark_converted(flac_path)

            if self.callback_complete:
                self.callback_complete(flac_path, success)

        runner = FFmpegProgress(cmd, on_update, on_complete)
        runner.run()

    # ----------------------------------------------------------------------
    # Folder Scanning
    # ----------------------------------------------------------------------
    def scan_for_flac(self, folders):
        flac_files = []

        for folder in folders:
            f = Path(folder)
            if not f.exists():
                continue
            flac_files.extend(list(f.rglob("*.flac")))

        return flac_files

    # ----------------------------------------------------------------------
    def shutdown(self):
        self.thread_pool.shutdown()
