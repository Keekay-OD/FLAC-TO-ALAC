import os
from concurrent.futures import ThreadPoolExecutor


def resolve_thread_count(performance_mode: str, override: int | None):
    cpu = os.cpu_count() or 4

    if override:
        return int(override)

    if performance_mode == "safe":
        return max(1, cpu // 4)

    if performance_mode == "balanced":
        return max(2, cpu // 2)

    if performance_mode == "max":
        return cpu

    return 4


class ConversionThreadPool:

    def __init__(self, performance_mode="balanced", threads_override=None):
        workers = resolve_thread_count(performance_mode, threads_override)
        print(f"[ThreadPool] Starting with {workers} workers")

        self.executor = ThreadPoolExecutor(max_workers=workers)

    def submit(self, fn, *args, **kwargs):
        return self.executor.submit(fn, *args, **kwargs)

    def shutdown(self):
        self.executor.shutdown(wait=False)
