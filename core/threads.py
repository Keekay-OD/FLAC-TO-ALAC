import os
from concurrent.futures import ThreadPoolExecutor


def get_thread_count(performance_mode: str, override: int | None = None):
    cpu = os.cpu_count() or 4

    if override:
        return override

    if performance_mode == "safe":
        return min(4, cpu // 2)

    if performance_mode == "balanced":
        return max(2, cpu - 2)

    if performance_mode == "max":
        return cpu

    return 4


import os
from concurrent.futures import ThreadPoolExecutor


class ConversionThreadPool:

    def __init__(self, performance_mode="balanced", threads_override=None):
        self.performance_mode = performance_mode
        self.override = threads_override

        # Determine number of workers
        if threads_override:
            workers = int(threads_override)

        elif performance_mode == "safe":
            workers = 1

        elif performance_mode == "balanced":
            workers = max(2, (os.cpu_count() or 4) // 2)

        elif performance_mode == "max":
            workers = os.cpu_count() or 8

        else:
            workers = 4

        self.max_workers = workers

        # ⭐ Create executor
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    # ------------------------------------------------------------------
    def submit(self, fn, *args, **kwargs):
        """Submit a job to the thread pool."""
        return self.executor.submit(fn, *args, **kwargs)

    # ------------------------------------------------------------------
    def shutdown(self, wait=True):
        """Shut down thread pool when closing app."""
        self.executor.shutdown(wait=wait)
