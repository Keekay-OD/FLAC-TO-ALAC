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

        # Resume file MUST be clean
        self.resume_state = self.load_resume_state()

        self.thread_pool = ConversionThreadPool(
            performance_mode=settings.get("performance_mode", "balanced"),
            threads_override=settings.get("threads_override")
        )

        # Callbacks injected by GUI
        self.callback_progress = None
        self.callback_complete = None

    # --------------------------------------------------------------
    # RESUME SYSTEM
    # --------------------------------------------------------------

    def load_resume_state(self):
        """Load resume info; if file invalid, reset it."""
        if not RESUME_FILE.exists():
            return {"converted": []}

        try:
            data = json.loads(RESUME_FILE.read_text())
            if "converted" not in data:
                return {"converted": []}
            # MUST be list
            if not isinstance(data["converted"], list):
                return {"converted": []}
            return data
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
        return str(path) in self.resume_state.get("converted", [])

    # --------------------------------------------------------------
    # QUEUE JOB
    # --------------------------------------------------------------

    def convert_file(self, flac_path: Path):
        """Always queue, but let worker decide skip."""
        return self.thread_pool.submit(self._convert_worker, flac_path)

    # --------------------------------------------------------------
    # WORKER FOR EACH FILE
    # --------------------------------------------------------------

    def _convert_worker(self, flac_path: Path):

        m4a_path = flac_path.with_suffix(".m4a")

        # ----------------------------------------------------------
        # FIX: ONLY SKIP if output file exists AND in resume list
        # ----------------------------------------------------------
        if m4a_path.exists() and self.already_converted(flac_path):
            if self.callback_complete:
                self.callback_complete(flac_path, True, skipped=True)
            return

        # Always allow conversion if resume file is empty
        metadata, cover = extract_flac_metadata(flac_path)

        cmd = [
            "ffmpeg",
            "-i", str(flac_path),
            "-c:a", "alac",
            "-progress", "pipe:1",
            "-nostats",
            "-y",
            str(m4a_path)
        ]

        # FFmpeg progress callback
        def on_update(info):
            if self.callback_progress:
                self.callback_progress(flac_path, info)

        def on_complete(success):
            if success:
                try:
                    write_alac_metadata(m4a_path, metadata, cover)
                except:
                    pass

                try:
                    self.history.add_record(
                        flac=str(flac_path),
                        alac=str(m4a_path),
                        metadata=metadata,
                        size_before=flac_path.stat().st_size,
                        size_after=m4a_path.stat().st_size
                    )
                except Exception as e:
                    print("History save failed:", e)

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

    # --------------------------------------------------------------
    # FOLDER SCANNING
    # --------------------------------------------------------------
    def scan_for_flac(self, folders):
        flac_files = []
        for folder in folders:
            fp = Path(folder)
            if fp.exists():
                flac_files.extend(fp.rglob("*.flac"))
        return flac_files

    def shutdown(self):
        self.thread_pool.shutdown()
