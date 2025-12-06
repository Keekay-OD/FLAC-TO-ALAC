import os
import traceback
from concurrent.futures import ThreadPoolExecutor, Future


def resolve_thread_count(performance_mode: str, override: int | None):
    cpu = os.cpu_count() or 8

    if override:
        return int(override)

    if performance_mode == "safe":
        return max(1, cpu // 4)

    if performance_mode == "balanced":
        return max(2, cpu // 2)

    if performance_mode == "max":
        return cpu

    return max(2, cpu // 2)


class ConversionThreadPool:

    def __init__(self, performance_mode="balanced", threads_override=None):

        self.max_workers = resolve_thread_count(performance_mode, threads_override)

        print(f"[ThreadPool] Starting with {self.max_workers} workers")

        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="vibes_worker"
        )

    # -----------------------------------------------------------
    def submit(self, fn, *args, **kwargs) -> Future:
        """Submit job with full crash reporting."""

        def wrapper():
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                print("\n\n[THREAD ERROR]")
                print(e)
                traceback.print_exc()
                return None

        return self.executor.submit(wrapper)

    # -----------------------------------------------------------
    def shutdown(self):
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
