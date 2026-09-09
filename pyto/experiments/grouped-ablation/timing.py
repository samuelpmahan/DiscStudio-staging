"""Wall-clock timing measured outside pyto.

`PcrRun` still carries no timing in the bytes this experiment retains: its fields
are `pcr`, `ticks`, `results` and the trailing `receipts` (pcr.py:130-145), and
`receipts` is empty unless `PCR.run` is called with `observe=True`. The Day 2 seam
does put a monotonic `started_ms`/`duration_ms` on each `Receipt` (pcr.py:118-119),
but those are `time.perf_counter()` values with an arbitrary origin, so they order
invocations inside one process and are not the wall-clock the run record reports.
That is what `timed` below measures, outside the library.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from features import FIXTURE_LABEL


def timed(label: str, fn: Callable[[], Any]) -> tuple[Any, dict]:
    start = time.perf_counter()
    value = fn()
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return value, {"label": label, "fixture": FIXTURE_LABEL, "wall_ms": round(elapsed_ms, 3), "clock": "time.perf_counter"}
