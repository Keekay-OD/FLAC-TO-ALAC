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


class ConversionThreadPool:
    """ThreadPool that manages all conversion jobs."""

    def __init__(self, performance_mode="balanced", override_threads=None):
        threads = get_thread_count(performance_mode, override_threads)
        self.pool = ThreadPoolExecutor(max_workers=threads)

    def submit(self, fn, *args, **kwargs):
        return self.pool.submit(fn, *args, **kwargs)

    def shutdown(self):
        self.pool.shutdown(wait=False)
