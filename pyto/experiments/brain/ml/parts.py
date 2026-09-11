"""parts in, parts out: the ml vertical, wired to the shared harness.

everything below is the harness's (`experiments/brain/harness.py`, owned by the
backend vertical). this module is the one import the ml vertical goes through, so
the wiring is in one place: it adds only what the vertical needs and the harness
does not owe it -- a whole-document view for saving, prefix helpers for PQL, and a
PCR built from a python callable instead of a ticks table.
"""

from __future__ import annotations

import os

try:  # as experiments.brain.ml.parts
    from .. import harness as H
except ImportError:  # as ml.parts, under `unittest discover -s experiments/brain`
    import harness as H

from pyto import PCR, PQL
from pyto.materialize import run_record, write_record

from .core import close as _close
from .core import max_error

STORE_DIR = H.STORE_DIR
RECORDS_DIR = H.RECORDS_DIR

dataset = H.dataset
synthetic = H.synthetic
oracle = H.oracle
bench = H.bench
bracket = H.bracket
judge = H.judge
decide = H.decide
refine = H.refine
finding = H.finding
map_part = H.map_part
navigate = H.navigate
territory = H.territory
result_address = H.result_address
H = H


def harness():
    return H


#: the keys of a run record that are a stopwatch reading rather than a fact about the run.
TIMING_KEYS = ("wall_ms", "duration_ms", "latency_ms", "tick_latency_ms")


def settle(record):
    """the same record with every wall-clock reading blanked, so the file is a function of the run.

    a record whose bytes change on every run cannot be committed: two branches that
    both re-ran the same program conflict on it, and a suite that regenerates it
    leaves the tree dirty behind every landing. the timings that are a claim live in
    the benchmark Parts, which say how many runs they are the median of; the timings
    in a record are one unrepeatable sample and are not worth a merge conflict.
    """
    if isinstance(record, dict):
        return {k: (None if k in TIMING_KEYS else settle(v)) for k, v in record.items()}
    if isinstance(record, list):
        return [settle(one) for one in record]
    return record


class Store(H.Store):
    """the harness store, plus the three things this vertical asks of it.

    `commit` is the harness's: false unless this is an explicit record run, so a
    test writes neither the tracked store nor the tracked records. a run record
    holds wall-clock durations, and one written into a tracked file leaves MAIN
    dirty, which land.sh refuses -- for whoever lands next, not for whoever wrote it.
    """

    def __init__(self, vertical="ml", pxc=None, commit=None, **kw):
        super().__init__(pxc=pxc, commit=commit, **kw)
        self.vertical = vertical

    # --- reading back, by prefix: the PQL the vertical actually asks ---
    def matches(self, prefix):
        return PQL.prefix(prefix).matches(self.pxc)

    def values(self, prefix):
        return PQL.prefix(prefix).values(self.pxc)

    def under(self, prefix):
        return PQL.prefix(prefix).addresses(self.pxc)

    def document(self):
        """every brain part this store holds, address -> value, sorted; receipts excluded."""
        return {address: self.pxc.get(address) for address in self.brain_addresses()}

    def save(self, vertical=None, path=None):
        """the store document, under whichever store_dir this store was given."""
        return super().save(vertical or self.vertical, path)

    # --- a PCR from a callable, for programs that are easier to write than to tabulate ---
    def run_program(self, name, build, record_name=None):
        pcr = PCR(name)
        build(pcr)
        preexisting = set(self.pxc.addresses())
        run = pcr.run(self.pxc, observe=True)
        import os

        os.makedirs(self.records_dir, exist_ok=True)
        record = settle(run_record(run, self.pxc, preexisting=preexisting))
        path = os.path.join(self.records_dir, f"{record_name or name}.json")
        write_record(record, path)
        self.records.append(path)
        for address in self.pxc.addresses():
            if address.startswith("px.exp.brain.") and address not in self.written:
                self.written.append(address)
        return run

    # kept for the vertical's own code: harness.Store.run takes a ticks table
    run = H.Store.run


def result(store, vertical, calc, case, value):
    """a calculation's answer, at the contract's result address."""
    return store.put(H.result_address(vertical, calc, case), value)


def close(got, expected, tolerance=1e-9):
    """the harness's comparison, in the vertical's one-value spelling."""
    return _close(got, expected, tolerance)
