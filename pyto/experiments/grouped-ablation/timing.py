"""Wall-clock timing measured outside pyto (PcrRun carries no timing: pcr.py:81-85)."""

from __future__ import annotations

import time
from typing import Any, Callable

from features import FIXTURE_LABEL


def timed(label: str, fn: Callable[[], Any]) -> tuple[Any, dict]:
    start = time.perf_counter()
    value = fn()
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return value, {"label": label, "fixture": FIXTURE_LABEL, "wall_ms": round(elapsed_ms, 3), "clock": "time.perf_counter"}
