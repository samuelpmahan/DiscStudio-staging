"""parts in, parts out: the ml vertical, wired to the shared harness.

everything below is the harness's (`experiments/brain/harness.py`, owned by the
backend vertical). this module is the one import the ml vertical goes through, so
the wiring is in one place: it adds only what the vertical needs and the harness
does not owe it -- a whole-document view for saving, prefix helpers for PQL, and a
PCR built from a python callable instead of a ticks table.
"""

from __future__ import annotations

import json
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


#: significant digits a stored float keeps. twelve, because numpy's accumulation order
#: differs between builds and the last ulp of a matmul is not a fact about the model:
#: 1e-15 of noise vanishes here and nothing anyone measured does.
DIGITS = 12

#: significant digits an oracle Part's `expected` and `got` keep. fewer, because an
#: oracle holds an outside library's answer as well as ours, and an iterative one
#: (scipy's optimiser, say) does not return the same last digits from two builds of
#: itself. eight is far more precision than any oracle here asserts on.
ORACLE_DIGITS = 8

#: how far below an oracle's own tolerance a number has to be before the oracle
#: stores it as the zero it is. a thousand times below: an oracle that asserts
#: agreement to 1e-9 is saying nothing at all about 1e-17, and 1e-17 is exactly
#: where two builds of numpy disagree -- an orthonormality check's off-diagonal,
#: for instance, which is 1.4e-18 on one machine and 7.4e-17 on another.
NOISE_FLOOR = 1e-3


def canonical(value, digits=None):
    """the same json-able value with every float rounded to DIGITS significant digits.

    a store document is compared against a fresh build -- by this vertical's own test,
    and by anyone reading the landing -- so it has to be a function of the calculation
    and not of which BLAS ran it. without this, numpy 2.5 and numpy 2.4 disagree by
    1.8e-15 on the same seeded regression and every address downstream of it differs.
    """
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return value
        out = float(f"{value:.{digits or DIGITS}g}")
        return 0.0 if out == 0.0 else out
    if isinstance(value, dict):
        return {k: canonical(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical(one, digits) for one in value]
    return value


def canonical_part(address, value):
    """one Part, made a function of the calculation rather than of the machine.

    an oracle Part is the exception twice over. its `expected` and `got` carry an
    outside library's numbers and keep eight digits, not twelve. and its
    `worst_relative_error` is a measurement of the distance between two floating
    point answers: at 1e-16 it is entirely the accumulation order of whichever BLAS
    ran, and no rounding makes it reproducible. so for an oracle that passed -- the
    only kind that lands -- the distance is dropped and the tolerance it came in
    under is what the Part says. a failing oracle keeps its number: that is the
    one time the exact distance is the point.
    """
    if not address.startswith("px.exp.brain.oracle.") or not isinstance(value, dict):
        return canonical(value)
    out = canonical(value, ORACLE_DIGITS)
    floor = abs(float(out.get("tolerance") or 0.0)) * NOISE_FLOOR
    if floor:
        out["expected"] = _snap(out.get("expected"), floor)
        out["got"] = _snap(out.get("got"), floor)
    if out.get("pass") and "worst_relative_error" in out:
        out["worst_relative_error"] = None
        out["within_tolerance"] = True
    return out


def _snap(value, floor):
    """anything smaller than `floor` is the zero the oracle already said it was."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        return 0.0 if abs(value) < floor else value
    if isinstance(value, dict):
        return {k: _snap(v, floor) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_snap(one, floor) for one in value]
    return value


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
    return canonical(record)


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
        """every brain part this store holds, address -> value, sorted, canonical for floats.

        canonical because this document is written to store/ml.json and compared
        against a fresh build: a value that differs in its last ulp between two
        numpy builds is the same value, and a document that says otherwise turns
        a landing on another machine red for nothing.
        """
        return {address: canonical_part(address, self.pxc.get(address))
                for address in self.brain_addresses()}

    def save(self, vertical=None, path=None):
        """this store's whole document, written whole -- not merged over the old file.

        the harness merges a save over what is already on disk, so that a vertical
        which loaded every store does not copy the others' parts into its own file.
        this vertical never loads another's, so its document is the complete set, and
        merging would mean a Part it renamed or withdrew lives on in the file forever
        with nothing left that produces it. writing whole is what makes a rename real.
        """
        vertical = vertical or self.vertical
        path = path or os.path.join(self.store_dir, f"{vertical}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        document = self.document()
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return path

    # --- a PCR from a callable, for programs that are easier to write than to tabulate ---
    def run_program(self, name, build, record_name=None):
        pcr = PCR(name)
        build(pcr)
        preexisting = set(self.pxc.addresses())
        run = pcr.run(self.pxc, observe=True)
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
