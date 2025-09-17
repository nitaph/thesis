import time
from contextlib import contextmanager

@contextmanager
def timer_ms():
    start = time.perf_counter()
    yield lambda: int((time.perf_counter() - start) * 1000)
