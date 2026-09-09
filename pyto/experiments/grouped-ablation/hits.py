"""A hit ledger over receipts, per the owner's answer (research/ULTRACODE-WEEK.md,
Reframing 4):

    "A hit is any Part or Calculation being used. Do not over-define it.
    Receipts already record reads and calls, so a hit ledger is: Parts read
    that existed before the run, and Calculations called that were already
    registered. No perceptual matching, no course identity, unless a later
    experiment needs it."

Two ledgers, both derived from receipts, nothing else:

- **A Part hit** is a `px:` read whose address this run had not itself produced
  yet -- the same rule `pyto.materialize.run_record`'s `hit` field applies
  (pyto/viewer/RECORD.md:53-56; pyto/src/pyto/materialize.py:238-240,286-288),
  reported here as its own ledger of (invocation, address) pairs rather than
  folded into a run record. A `fn:` read (a same-run result) is never a Part
  hit -- that Part was computed by this run, not reused from before it.
- **A Calculation hit** is an invocation whose Calculation address had already
  been used by an earlier invocation in the same run -- the second and later
  `fit`/`score` invocations across the grouped ablation's six variants, for
  instance. `PxC.register` is a no-op the second time an address is registered
  with the same `calculate` (core.py:69-72: "already registered" raises only on
  a *different* callable at the same address) -- a Calculation hit is exactly
  that no-op case. The first invocation of an address is never a Calculation
  hit; it is the one that registers it.

`hit_ledger(record_or_run)` accepts either shape, in the order receipts/the
record already carry (execution order -- `PcrRun.receipts` is populated in that
order by `PCR.run`, pcr.py:284-378; a `pyto-run-record@1` document's
`ticks[].invocations[]` is Tick order then declaration order):

- a `pyto.pcr.PcrRun` with `observe=True` receipts (`PcrRun.receipts`); or
- a `pyto-run-record@1` dict (pyto/viewer/RECORD.md) with `declared_consumes`
  spelled `px:<address>` the way `pyto.materialize.run_record` writes it.

Without receipts -- a `PcrRun` from `PCR.run(pxc, observe=False)`, or a record
whose invocations carry no `declared_consumes` -- there is nothing to count
from, and every count comes back zero; this module never falls back to the
authored testimony (which has no digests, no timing and no declared/actual
split) to guess at what happened.
"""

from __future__ import annotations

from typing import Any, Iterable, Iterator

from pyto import PcrRun

_Row = tuple[str | None, str, tuple[str, ...], tuple[str, ...]]


def _rows_from_record(record: dict) -> Iterator[_Row]:
    for tick in record.get("ticks", ()):
        for invocation in tick.get("invocations", ()):
            calculation_address = invocation["calculation"]["address"]
            declared = tuple(
                spelling.removeprefix("px:")
                for spelling in (invocation.get("declared_consumes") or ())
                if spelling.startswith("px:")
            )
            writes = tuple(write["address"] for write in (invocation.get("writes") or ()))
            yield invocation.get("id"), calculation_address, declared, writes


def _rows_from_run(run: PcrRun) -> Iterator[_Row]:
    for receipt in run.receipts.values():
        writes = tuple(write.address for write in receipt.writes)
        yield receipt.invocation_id, receipt.calculation.address, receipt.declared_consumes, writes


def _rows(record_or_run: Any) -> Iterable[_Row]:
    if isinstance(record_or_run, PcrRun):
        return _rows_from_run(record_or_run)
    if isinstance(record_or_run, dict):
        return _rows_from_record(record_or_run)
    raise TypeError(
        "hit_ledger: expected a pyto.pcr.PcrRun or a pyto-run-record@1 dict, "
        f"got {type(record_or_run).__name__}"
    )


def hit_ledger(record_or_run: Any) -> dict:
    """{"part_hits": [{"invocation_id", "address"}, ...],
        "calculation_hits": [{"invocation_id", "calculation"}, ...],
        "counters": {"invocations", "part_hits", "calculation_hits"}}

    Every entry names the invocation id it came from, so the ledger reads as a
    trace (which invocation reused what), not only a count.
    """
    part_hits: list[dict[str, str]] = []
    calculation_hits: list[dict[str, str]] = []
    produced_so_far: set[str] = set()
    seen_calculations: set[str] = set()
    total = 0

    for invocation_id, calculation_address, declared_consumes, writes in _rows(record_or_run):
        total += 1
        if calculation_address in seen_calculations:
            calculation_hits.append({"invocation_id": invocation_id, "calculation": calculation_address})
        seen_calculations.add(calculation_address)

        for address in declared_consumes:
            if address not in produced_so_far:
                part_hits.append({"invocation_id": invocation_id, "address": address})
        produced_so_far.update(writes)

    return {
        "part_hits": part_hits,
        "calculation_hits": calculation_hits,
        "counters": {
            "invocations": total,
            "part_hits": len(part_hits),
            "calculation_hits": len(calculation_hits),
        },
    }
