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

        # Resume tracking
        self.resume_state = self.load_resume_state()

        # Thread pool
        self.thread_pool = ConversionThreadPool(
            performance_mode=settings.get("performance_mode", "balanced"),
            threads_override=settings.get("threads_override")
        )

    # ------------------------------------------------------------------
    # RESUME SYSTEM
    # ------------------------------------------------------------------
    def load_resume_state(self):
        if not RESUME_FILE.exists():
            return {"files": {}}

        try:
            data = json.loads(RESUME_FILE.read_text())
        except:
            return {"files": {}}

        if "files" not in data:
            data["files"] = {}

        return data

    def save_resume_state(self):
        RESUME_FILE.write_text(json.dumps(self.resume_state, indent=4))

    def file_changed(self, flac_path: Path):
        key = str(flac_path)
        stat = flac_path.stat()
        info = {"mtime": stat.st_mtime, "size": stat.st_size}

        previous = self.resume_state["files"].get(key)

        # First time processing
        if previous is None:
            self.resume_state["files"][key] = info
            self.save_resume_state()
            return True

        changed = (
            previous["mtime"] != info["mtime"] or
            previous["size"] != info["size"]
        )

        # Always update stored state
        self.resume_state["files"][key] = info
        self.save_resume_state()

        return changed

    # ------------------------------------------------------------------
    def convert_file(self, flac_path: Path):
        return self.thread_pool.submit(self._worker, flac_path)

    # ------------------------------------------------------------------
    def _worker(self, flac_path: Path):
        from core.event_bus import event_bus

        m4a_path = flac_path.with_suffix(".m4a")

        # SKIP
        if not self.file_changed(flac_path) and m4a_path.exists():
            print("[SKIP]", flac_path)
            if self.callback_complete:
                self.callback_complete(flac_path, True, True)
            event_bus.conversion_finished.emit(str(flac_path), True)
            return

        # Metadata
        metadata, cover = extract_flac_metadata(flac_path)

        # FFmpeg command
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "warning",
            "-vn",                # <--- discard ALL video streams
            "-sn",                # discard subtitles (if any)
            "-dn",                # discard data streams
            "-i", str(flac_path),

            "-map", "0:a:0",      # FORCE map only the first audio stream
            "-c:a", "alac",
            "-movflags", "+faststart",

            "-progress", "pipe:1",
            "-y",
            str(m4a_path),
        ]


        # UPDATE
        def on_update(info):
            if "out_time_ms" not in info:
                return

            try:
                ms = int(info["out_time_ms"])
                pct = max(0, min(100, (ms / 120_000) * 100))  # use real progress
            except:
                pct = 0

            if self.callback_progress:
                self.callback_progress(flac_path, pct)

        # COMPLETE
        def on_complete(success):
            skipped = False

            if success:
                try:
                    write_alac_metadata(m4a_path, metadata, cover)
                except Exception as e:
                    print("[Metadata ERROR]", e)

                # Add to history
                if self.history:
                    self.history.add_record(
                        flac=str(flac_path),
                        alac=str(m4a_path),
                        metadata=metadata,
                        size_before=flac_path.stat().st_size,
                        size_after=m4a_path.stat().st_size
                    )

                # Delete original
                if self.settings.get("delete_originals", False):
                    try:
                        flac_path.unlink()
                    except:
                        pass

                # Save resume
                self.file_changed(flac_path)

            if self.callback_complete:
                self.callback_complete(flac_path, success, skipped)

            event_bus.conversion_finished.emit(str(flac_path), success)

        # RUN FFmpeg
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
