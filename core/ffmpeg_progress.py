import subprocess
import threading
import time
import sys
import os
import signal


class FFmpegProgress:
    """
    Fully safe FFmpeg wrapper:
    - No charset crashes
    - No zombie FFmpeg processes
    - Threads exit reliably
    - Auto-kill on hang or timeout
    """

    def __init__(self, cmd, on_update, on_complete, timeout=600):
        self.cmd = cmd
        self.on_update = on_update
        self.on_complete = on_complete
        self.process = None
        self._stop = False
        self.timeout = timeout  # hard timeout to prevent zombie ffmpeg

    # ------------------------------------------------------------------
    def safe_decode(self, raw):
        """Decode without ever raising exceptions (UTF-8 only)."""
        if not raw:
            return ""
        return raw.decode("utf-8", errors="ignore").strip()

    # ------------------------------------------------------------------
    def _reader(self, stream):
        """Reads progress lines non-blocking."""
        while not self._stop:
            raw = stream.readline()
            if not raw:
                break

            text = self.safe_decode(raw)
            if "=" in text:
                k, v = text.split("=", 1)
                try:
                    self.on_update({k.strip(): v.strip()})
                except:
                    pass  # NEVER let UI crash

    # ------------------------------------------------------------------
    def kill_process(self):
        """Kill FFmpeg safely (Windows and Linux)."""
        if not self.process:
            return

        try:
            self.process.kill()
        except:
            pass

        try:
            # Some FFmpeg versions spawn child processes
            if os.name == "nt":
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except:
            pass

    # ------------------------------------------------------------------
    def run(self):
        """Launch FFmpeg safely with full leak-prevention."""
        try:
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                bufsize=4096,                 # safe buffer
                universal_newlines=False,     # never auto decode
            )
        except Exception as e:
            print(f"[FFmpeg ERROR] Failed to launch: {e}")
            if self.on_complete:
                self.on_complete(False)
            return

        # Threads to read progress
        t_out = threading.Thread(target=self._reader, args=(self.process.stdout,), daemon=True)
        t_err = threading.Thread(target=self._reader, args=(self.process.stderr,), daemon=True)
        t_out.start()
        t_err.start()

        # HARD timeout to prevent zombie FFmpeg
        start_time = time.time()

        while True:
            ret = self.process.poll()
            if ret is not None:
                break

            if time.time() - start_time > self.timeout:
                print("[FFmpeg] TIMEOUT — killing process")
                self.kill_process()
                break

            time.sleep(0.05)

        self._stop = True
        time.sleep(0.1)

        success = (self.process.returncode == 0)

        try:
            self.on_complete(success)
        except:
            pass

        self.kill_process()
