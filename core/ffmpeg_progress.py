import subprocess
import threading


class FFmpegProgress:
    """
    Runs FFmpeg and emits progress callbacks.

    Callback signature:
        on_update(output_dict)
        on_complete(success: bool)
    """

    def __init__(self, cmd, on_update=None, on_complete=None):
        self.cmd = cmd
        self.on_update = on_update
        self.on_complete = on_complete
        self.process = None

    def run(self):
        self.process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True
        )

        # Parse ffmpeg progress lines
        for line in self.process.stdout:
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                if self.on_update:
                    self.on_update({key: value})

        self.process.wait()
        success = (self.process.returncode == 0)

        if self.on_complete:
            self.on_complete(success)

    def start(self):
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
