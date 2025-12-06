import subprocess
from pathlib import Path
import json
import time

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
            threads_override=settings.get("threads_override")
        )

        # callbacks (GUI injected)
        self.callback_progress = None
        self.callback_complete = None

    # --------------------------------------------------------------
    # Resume save/load
    # --------------------------------------------------------------
    def load_resume_state(self):
        if not RESUME_FILE.exists():
            return {"converted": []}

        try:
            data = json.loads(RESUME_FILE.read_text())
            if isinstance(data.get("converted"), list):
                return data
        except:
            pass

        return {"converted": []}

    def save_resume_state(self):
        RESUME_FILE.write_text(json.dumps(self.resume_state, indent=4))

    def mark_converted(self, path: Path):
        p = str(path)
        if p not in self.resume_state["converted"]:
            self.resume_state["converted"].append(p)
            self.save_resume_state()

    def already_converted(self, path: Path):
        return str(path) in self.resume_state["converted"]

    # --------------------------------------------------------------
    # Queue conversion
    # --------------------------------------------------------------
    def convert_file(self, flac_path: Path):
        print(f"[Queue] {flac_path}")
        return self.thread_pool.submit(self._convert_worker, flac_path)

    # --------------------------------------------------------------
    # Worker
    # --------------------------------------------------------------
    def _convert_worker(self, flac_path: Path):

        m4a_path = flac_path.with_suffix(".m4a")

        # Skip if already converted
        if m4a_path.exists() and self.already_converted(flac_path):
            if self.callback_complete:
                self.callback_complete(flac_path, True, skipped=True)
            return

        metadata, cover = extract_flac_metadata(flac_path)

        duration_seconds = metadata.get("DURATION_SECONDS")  # provided by extractor
        if not duration_seconds:
            duration_seconds = 0

        cmd = [
            "ffmpeg",
            "-i", str(flac_path),
            "-c:a", "alac",
            "-progress", "pipe:1",
            "-nostats",
            "-y",
            str(m4a_path)
        ]

        # --------------- PROGRESS HANDLER --------------------------
        def on_update(info):
            if "out_time_ms" in info:
                ms = int(info["out_time_ms"])
                if duration_seconds > 0:
                    pct = min(100, (ms / (duration_seconds * 1000)) * 100)
                else:
                    pct = 0

                if self.callback_progress:
                    self.callback_progress(flac_path, pct)

        # --------------- COMPLETION HANDLER ------------------------
        def on_complete(success):
            if success:
                write_alac_metadata(m4a_path, metadata, cover)

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

                # Delete original
                if self.settings.get("delete_originals", False):
                    try:
                        flac_path.unlink()
                        print(f"[Delete] Removed FLAC: {flac_path}")
                    except Exception as e:
                        print(f"[Delete ERROR] Cannot delete {flac_path}: {e}")

                self.mark_converted(flac_path)

                # Auto-remove empty folder
                parent = flac_path.parent
                try:
                    if not any(parent.iterdir()):
                        parent.rmdir()
                        print(f"[Cleanup] Deleted empty folder: {parent}")
                except:
                    pass

            if self.callback_complete:
                self.callback_complete(flac_path, success)

        runner = FFmpegProgress(cmd, on_update, on_complete)
        runner.run()

    # --------------------------------------------------------------
    # Folder scanning
    # --------------------------------------------------------------
    def scan_for_flac(self, folders):
        collected = []
        for folder in folders:
            p = Path(folder)
            if p.exists():
                collected.extend(p.rglob("*.flac"))
        return collected

    def shutdown(self):
        self.thread_pool.shutdown()
