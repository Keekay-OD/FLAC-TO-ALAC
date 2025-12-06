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

        # MUST initialize resume system FIRST
        self.resume_state = self.load_resume_state()

        # Thread pool for conversions
        self.thread_pool = ConversionThreadPool(
            performance_mode=settings.get("performance_mode", "balanced"),
            threads_override=settings.get("threads_override")
        )


    # ------------------------------------------------------------------
    def load_resume(self):
        if RESUME_FILE.exists():
            try:
                return json.loads(RESUME_FILE.read_text())
            except:
                pass
        return {"files": {}}

    def save_resume(self):
        RESUME_FILE.write_text(json.dumps(self.resume, indent=4))

    # ------------------------------------------------------------------
    def file_changed(self, path: Path):
        """Return True if file size OR timestamp changed."""
        key = str(path)
        stat = path.stat()
        size = stat.st_size
        mtime = stat.st_mtime

        old = self.resume["files"].get(key)
        if not old:
            return True  # never converted

        if old["size"] != size:
            return True

        if abs(old["mtime"] - mtime) > 0.0001:
            return True

        return False

    def store_file_state(self, path: Path):
        stat = path.stat()
        self.resume["files"][str(path)] = {
            "size": stat.st_size,
            "mtime": stat.st_mtime
        }
        self.save_resume()

    # ------------------------------------------------------------------



# --------------------------------------------------------------
# RESUME SYSTEM (fixed)
# --------------------------------------------------------------

    def load_resume_state(self):
        """Load resume tracking file (auto-repair if missing fields)."""
        if not RESUME_FILE.exists():
            return {"files": {}, "converted": []}

        try:
            data = json.loads(RESUME_FILE.read_text())
        except:
            return {"files": {}, "converted": []}

        # Auto-fix missing fields
        if "files" not in data or not isinstance(data["files"], dict):
            data["files"] = {}
        if "converted" not in data or not isinstance(data["converted"], list):
            data["converted"] = []

        return data


    def save_resume_state(self):
        RESUME_FILE.write_text(json.dumps(self.resume_state, indent=4))


    def file_changed(self, flac_path: Path):
        """Return True if file was modified since last run."""
        key = str(flac_path)

        mtime = flac_path.stat().st_mtime
        size = flac_path.stat().st_size

        previous = self.resume_state["files"].get(key)

        # First time seeing file → treat as changed
        if previous is None:
            self.resume_state["files"][key] = {"mtime": mtime, "size": size}
            self.save_resume_state()
            return True

        # Compare old vs new
        changed = (previous["mtime"] != mtime) or (previous["size"] != size)

        # Update stored values
        self.resume_state["files"][key] = {"mtime": mtime, "size": size}
        self.save_resume_state()

        return changed







    def convert_file(self, flac_path: Path):
        return self.thread_pool.submit(self._worker, flac_path)

    # ------------------------------------------------------------------
    def _worker(self, flac_path: Path):

        m4a_path = flac_path.with_suffix(".m4a")

        # --------- SKIP if unchanged ----------
        if not self.file_changed(flac_path) and m4a_path.exists():
            print("[SKIP] Already converted:", flac_path)
            from core.event_bus import event_bus
            event_bus.conversion_finished.emit(str(flac_path), True)
            return

        # --------- Metadata extraction ----------
        metadata, cover = extract_flac_metadata(flac_path)

        # --------- Build ffmpeg command ----------
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(flac_path),
            "-c:a", "alac",
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-y",
            str(m4a_path),
        ]

        # --------- Progress callback ----------
        def on_update(info):
            if "out_time_ms" in info:
                try:
                    ms = int(info["out_time_ms"])
                    percent = min(100, int(ms / 50000))
                except:
                    percent = 0

                from core.event_bus import event_bus
                event_bus.progress_updated.emit(str(flac_path), percent)

        # --------- Completion callback ----------
        def on_complete(success):
            from core.event_bus import event_bus

            if success:
                # write metadata
                write_alac_metadata(m4a_path, metadata, cover)

                # history
                self.history.add_record(
                    flac=str(flac_path),
                    alac=str(m4a_path),
                    metadata=metadata,
                    size_before=flac_path.stat().st_size,
                    size_after=m4a_path.stat().st_size
                )

                # delete original?
                if self.settings.get("delete_originals", False):
                    try:
                        flac_path.unlink()
                    except:
                        pass

                self.store_file_state(flac_path)

            event_bus.conversion_finished.emit(str(flac_path), success)

        # --------- RUN SAFE FFmpeg ----------
        runner = FFmpegProgress(cmd, on_update, on_complete)
        runner.run()

    # ------------------------------------------------------------------
    def scan_for_flac(self, folders):
        flacs = []
        for folder in folders:
            p = Path(folder)
            if p.exists():
                flacs.extend(p.rglob("*.flac"))
        return flacs
