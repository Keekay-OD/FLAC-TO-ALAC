import subprocess
import time
import threading


class FFmpegProgress:
    """
    Runs FFmpeg and monitors its -progress output.
    Calls:
        on_update(dict | pct | whatever)
        on_complete(bool)
    """

    def __init__(self, ffmpeg_cmd, on_update, on_complete):
        self.cmd = ffmpeg_cmd
        self.on_update = on_update
        self.on_complete = on_complete

        self.start_time = None
        self.duration_ms = None
        self.last_timestamp = 0

    # ---------------------------------------------------------
    # Parse FFmpeg progress lines
    # ---------------------------------------------------------
    def parse_line(self, line: str):
        if "=" not in line:
            return None
        key, value = line.strip().split("=", 1)
        return key, value

    # ---------------------------------------------------------
    # Convert FFmpeg "hh:mm:ss.ms" → milliseconds
    # ---------------------------------------------------------
    def ts_to_ms(self, ts: str):
        try:
            h, m, s = ts.split(":")
            s, ms = s.split(".")
            total = (
                int(h) * 3600000 +
                int(m) * 60000 +
                int(s) * 1000 +
                int(ms)
            )
            return total
        except:
            return 0

    # ---------------------------------------------------------
    # Thread target
    # ---------------------------------------------------------
    def _run(self):
        self.start_time = time.time()

        process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        try:
            while True:
                line = process.stdout.readline()
                if not line:
                    break

                parsed = self.parse_line(line)
                if not parsed:
                    continue

                key, value = parsed

                # ---------------------------------------------
                # Extract duration (only once)
                # ---------------------------------------------
                if key == "duration":  
                    try:
                        self.duration_ms = int(value)
                    except:
                        self.duration_ms = None

                # ---------------------------------------------
                # Get timestamp updates
                # ---------------------------------------------
                if key == "out_time_us" or key == "out_time_ms":
                    try:
                        current_ms = int(value)
                        self.last_timestamp = current_ms
                    except:
                        continue

                    if self.duration_ms:
                        pct = (current_ms / self.duration_ms) * 100
                        pct = min(100.0, pct)
                    else:
                        pct = 0.0

                    elapsed = time.time() - self.start_time

                    if current_ms > 0 and self.duration_ms and current_ms > 0:
                        remaining_ms = self.duration_ms - current_ms
                        speed = current_ms / (elapsed * 1000)
                        eta = remaining_ms / 1000 / speed if speed > 0 else None
                    else:
                        eta = None
                        speed = None

                    self.on_update({
                        "pct": pct,
                        "elapsed": elapsed,
                        "eta": eta,
                        "speed": speed
                    })

                # Marks completion without closing
                if key == "progress" and value == "end":
                    break

        except Exception as e:
            print("[FFmpeg ERROR]", e)

        finally:
            process.wait()
            self.on_complete(process.returncode == 0)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def run(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
