import json
from pathlib import Path
from datetime import datetime

from core.ffmpeg_progress import FFmpegProgress
from core.metadata import extract_flac_metadata, write_alac_metadata
from core.threads import ConversionThreadPool
from utils.paths import RESUME_FILE


class ConversionManager:

    def __init__(self, settings, history_manager):
        self.settings = settings
        self.history = history_manager

        self.callback_progress = None
        self.callback_complete = None

        self.resume_state = self.load_resume_state()

        self.thread_pool = ConversionThreadPool(
            performance_mode=settings.get("performance_mode", "balanced"),
            threads_override=settings.get("threads_override")
        )

    # --------------------------------------------------------------
    def load_resume_state(self):
        if not RESUME_FILE.exists():
            return {"files": {}, "converted": []}

        try:
            data = json.loads(RESUME_FILE.read_text())
        except:
            return {"files": {}, "converted": []}

        if "files" not in data:
            data["files"] = {}

        if "converted" not in data:
            data["converted"] = []

        return data

    def save_resume_state(self):
        RESUME_FILE.write_text(json.dumps(self.resume_state, indent=4))

    # --------------------------------------------------------------
    def file_changed(self, flac_path: Path):
        key = str(flac_path)
        stat = flac_path.stat()
        size = stat.st_size
        mtime = stat.st_mtime

        old = self.resume_state["files"].get(key)

        if old is None:
            self.resume_state["files"][key] = {"size": size, "mtime": mtime}
            self.save_resume_state()
            return True

        changed = (old["size"] != size or old["mtime"] != mtime)

        self.resume_state["files"][key] = {"size": size, "mtime": mtime}
        self.save_resume_state()

        return changed

    # --------------------------------------------------------------
    def convert_file(self, flac_path: Path):
        return self.thread_pool.submit(self._worker, flac_path)

    # --------------------------------------------------------------
    def _worker(self, flac_path: Path):
        m4a_path = flac_path.with_suffix(".m4a")

        # SKIP if unchanged and already encoded
        if not self.file_changed(flac_path) and m4a_path.exists():
            if self.callback_complete:
                self.callback_complete(flac_path, True, True)
            return

        metadata, cover = extract_flac_metadata(flac_path)

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-i", str(flac_path),
            "-vn",
            "-c:a", "alac",
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-y",
            str(m4a_path),
        ]

        def on_update(info):
            if "out_time_ms" in info and self.callback_progress:
                try:
                    ms = int(info["out_time_ms"])
                    pct = min(100, ms / 50000 * 100)
                except:
                    pct = 0
                self.callback_progress(flac_path, pct)

        def on_complete(success):
            if success:
                write_alac_metadata(m4a_path, metadata, cover)

                if self.history:
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

            if self.callback_complete:
                self.callback_complete(flac_path, success, False)

        runner = FFmpegProgress(cmd, on_update, on_complete)
        runner.run()

    # --------------------------------------------------------------
    def scan_for_flac(self, folders):
        flacs = []
        for folder in folders:
            p = Path(folder)
            if p.exists():
                flacs.extend(p.rglob("*.flac"))
        return flacs
