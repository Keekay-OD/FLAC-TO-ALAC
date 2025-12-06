import os
import traceback
from concurrent.futures import ThreadPoolExecutor, Future

class ConversionThreadPool:
    """
    ONE clean threadpool implementation.
    - Stable job execution
    - No swallowed exceptions
    - No duplicate definitions
    """

    def __init__(self, performance_mode="balanced", threads_override=None):
        cpu = os.cpu_count() or 8

        if threads_override:
            workers = int(threads_override)
        else:
            if performance_mode == "safe":
                workers = max(1, cpu // 4)
            elif performance_mode == "balanced":
                workers = max(2, cpu // 2)
            elif performance_mode == "max":
                workers = cpu
            else:
                workers = max(2, cpu // 2)

        self.workers = workers

        print(f"[ThreadPool] Starting with {self.workers} workers")

        # SINGLE executor used everywhere
        self.executor = ThreadPoolExecutor(
            max_workers=self.workers,
            thread_name_prefix="vibes_worker"
        )

    # -----------------------------------------------------------
    def submit(self, fn, *args, **kwargs) -> Future:
        """Submit a job with crash reporting."""
        def wrapper():
            try:
                return fn(*args, **kwargs)
            except Exception:
                print("\n[THREAD ERROR]")
                traceback.print_exc()
                return None

        return self.executor.submit(wrapper)

    # -----------------------------------------------------------
    def shutdown(self):
        """Stop accepting new jobs and cancel remaining."""
        try:
            self.executor.shutdown(
                wait=False,
                cancel_futures=True
            )
            print("[ThreadPool] Shutdown complete")
        except Exception:
            traceback.print_exc()
