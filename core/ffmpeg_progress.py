import subprocess
import threading
import time
import os


class FFmpegProgress:

    def __init__(self, cmd, on_update, on_complete, timeout=600):
        self.cmd = cmd
        self.on_update = on_update
        self.on_complete = on_complete
        self.timeout = timeout
        self.process = None
        self._stop = False

    def decode(self, raw):
        if not raw:
            return ""
        return raw.decode("utf-8", errors="ignore").strip()

    def _reader(self, stream, label):
        while not self._stop:
            raw = stream.readline()
            if not raw:
                break

            text = self.decode(raw)
            if text:
                print(f"[FFmpeg {label}] {text}")

            if "=" in text:
                k, v = text.split("=", 1)
                try:
                    self.on_update({k.strip(): v.strip()})
                except:
                    pass


    def kill(self):
        if not self.process:
            return
        try:
            self.process.kill()
        except:
            pass

        if os.name == "nt":
            try:
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except:
                pass

    def run(self):
        try:
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                universal_newlines=False,
                bufsize=4096
            )
        except Exception as e:
            print("[FFmpeg ERROR]", e)
            try:
                self.on_complete(False)
            except:
                pass
            return

        t1 = threading.Thread(target=self._reader, args=(self.process.stdout, "OUT"), daemon=True)
        t2 = threading.Thread(target=self._reader, args=(self.process.stderr, "ERR"), daemon=True)

        t1.start()
        t2.start()

        start = time.time()

        while True:
            ret = self.process.poll()
            if ret is not None:
                break

            if time.time() - start > self.timeout:
                print("[FFmpeg TIMEOUT] Killing process")
                self.kill()
                break

            time.sleep(0.05)

        self._stop = True
        time.sleep(0.1)

        success = (self.process.returncode == 0)

        try:
            self.on_complete(success)
        except:
            pass

        self.kill()
