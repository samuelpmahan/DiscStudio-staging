"""parts in, parts out: the ml vertical's store, oracle, benchmark, bracket and finding writers.

this is the vertical's own copy of the contract's harness surface, written so the
shared `experiments/brain/harness.py` can replace it without touching a caller:
`use_harness()` binds to it when it lands and every writer below delegates.
until then this file is the harness for the ml vertical and nothing else uses it.
"""

from __future__ import annotations

import json
import os
import time

from pyto import PCR, PQL, Part, PxC
from pyto.materialize import run_record, write_record

from .core import close, max_error

BRAIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_DIR = os.path.join(BRAIN, "store")
RECORDS_DIR = os.path.join(BRAIN, "records")

_HARNESS = None


def use_harness(module=None):
    """bind to the shared harness when it has landed; returns what is bound."""
    global _HARNESS
    if module is None:
        try:
            from .. import harness as module  # type: ignore[no-redef]
        except Exception:
            try:
                import harness as module  # type: ignore[no-redef]
            except Exception:
                module = None
    _HARNESS = module
    return _HARNESS


def harness():
    return _HARNESS


class Store:
    """a PxC with the vertical's file discipline: put, get, save, load, run."""

    def __init__(self, vertical="ml", pxc=None):
        self.vertical = vertical
        self.pxc = pxc if pxc is not None else PxC()

    # --- values ---
    def put(self, address, value):
        self.pxc.set(Part(address), value)
        return address

    def get(self, address):
        return self.pxc.get(address)

    def has(self, address):
        return self.pxc.has(address)

    def addresses(self, prefix=None):
        if prefix is None:
            return self.pxc.addresses()
        return PQL.prefix(prefix).addresses(self.pxc)

    def values(self, prefix):
        return PQL.prefix(prefix).values(self.pxc)

    def matches(self, prefix):
        return PQL.prefix(prefix).matches(self.pxc)

    # --- files ---
    def document(self):
        """every non-receipt part this store holds, address -> value, sorted."""
        return {
            address: self.pxc.get(address)
            for address in self.pxc.addresses()
            if not address.startswith("px.receipt.")
        }

    def save(self, name=None):
        os.makedirs(STORE_DIR, exist_ok=True)
        path = os.path.join(STORE_DIR, f"{name or self.vertical}.json")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(self.document(), handle, indent=2, sort_keys=True)
            handle.write("\n")
        return path

    def load(self, path):
        with open(path, encoding="utf-8") as handle:
            for address, value in json.load(handle).items():
                self.put(address, value)
        return self

    def load_store(self):
        """merge every store/*.json, the way the shared harness will."""
        if not os.path.isdir(STORE_DIR):
            return self
        for name in sorted(os.listdir(STORE_DIR)):
            if name.endswith(".json"):
                self.load(os.path.join(STORE_DIR, name))
        return self

    # --- runs ---
    def run(self, name, build, record_name=None):
        """build a PCR with `build(pcr)`, run it observed, write the record."""
        pcr = PCR(name)
        build(pcr)
        before = set(self.pxc.addresses())
        run = pcr.run(self.pxc, observe=True)
        os.makedirs(RECORDS_DIR, exist_ok=True)
        record = run_record(run, self.pxc, preexisting=before, pcr_name=name)
        path = os.path.join(RECORDS_DIR, f"{record_name or name}.json")
        write_record(record, path)
        return run


# --- the part writers --------------------------------------------------------


def result(store, vertical, calc, case, value):
    return store.put(f"px.exp.brain.result.{vertical}.{calc}.{case}", value)


def oracle(store, vertical, calc, case, got, expected, reference, tolerance=1e-9, for_=""):
    """the oracle part: a reference, what it said, what we said, and the verdict."""
    if _HARNESS is not None and hasattr(_HARNESS, "oracle"):
        return _HARNESS.oracle(store, vertical, calc, case, got, expected, reference, tolerance, for_)
    passed = close(got, expected, tolerance)
    store.put(
        f"px.exp.brain.oracle.{vertical}.{calc}.{case}",
        {
            "for": for_,
            "calc": f"fn.brain.{vertical}.{calc}",
            "reference": reference,
            "expected": expected,
            "got": got,
            "tolerance": tolerance,
            "max_error": max_error(got, expected),
            "pass": bool(passed),
        },
    )
    return bool(passed)


def bench(store, vertical, calc, backend, size, fn, n=7, for_=""):
    """n wall-clock runs of fn; the median and the min, as a part.

    perf_counter is allowed here: this is the host, not a calculation.
    """
    if _HARNESS is not None and hasattr(_HARNESS, "bench"):
        return _HARNESS.bench(store, vertical, calc, backend, size, fn, n, for_)
    timings = []
    out = None
    for _ in range(n):
        start = time.perf_counter()
        out = fn()
        timings.append((time.perf_counter() - start) * 1000.0)
    timings.sort()
    address = f"px.exp.brain.bench.{vertical}.{calc}.{backend}.{size}"
    store.put(
        address,
        {
            "for": for_,
            "backend": backend,
            "size": str(size),
            "n": n,
            "wall_ms_median": timings[len(timings) // 2],
            "wall_ms_min": timings[0],
            "inputs_sha256": _digest(size),
        },
    )
    return store.get(address), out


def _digest(value):
    import hashlib

    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def bracket(store, vertical, problem, criteria, candidates, for_=""):
    """the bracket part. criteria are written here, BEFORE any judging."""
    address = f"px.exp.brain.bracket.{vertical}.{problem}"
    store.put(
        address,
        {
            "for": for_,
            "problem": problem,
            "criteria": list(criteria),
            "candidates": list(candidates),
            "judged": [],
            "winner": None,
            "refined": False,
        },
    )
    return address


def judge(store, vertical, problem, judge_name, candidate, scores, note=""):
    address = f"px.exp.brain.bracket.{vertical}.{problem}"
    value = dict(store.get(address))
    if not value["criteria"]:
        raise ValueError("a bracket with no criteria cannot be judged: write the criteria first")
    judged = list(value["judged"])
    judged.append({"judge": judge_name, "candidate": candidate, "scores": dict(scores), "note": note})
    value["judged"] = judged
    store.put(address, value)
    return value


def decide(store, vertical, problem):
    """the winner, from the recorded scores, by the recorded criteria and their weights."""
    address = f"px.exp.brain.bracket.{vertical}.{problem}"
    value = dict(store.get(address))
    weights = {c["name"]: c.get("weight", 1.0) for c in value["criteria"]}
    totals = {}
    for row in value["judged"]:
        total = sum(weights.get(k, 0.0) * float(v) for k, v in row["scores"].items())
        totals.setdefault(row["candidate"], []).append(total)
    if not totals:
        return None
    averaged = {k: sum(v) / len(v) for k, v in totals.items()}
    winner = max(sorted(averaged), key=lambda k: averaged[k])
    value["winner"] = winner
    value["totals"] = averaged
    store.put(address, value)
    return winner


def finding(store, vertical, k, kind, text, for_, workaround=None, proposal=None):
    if kind not in ("strength", "friction"):
        raise ValueError("a finding is a strength or a friction")
    address = f"proposal.brain.{vertical}.{k}"
    value = {"for": for_, "kind": kind, "text": text}
    if workaround:
        value["workaround"] = workaround
    if proposal:
        value["proposal"] = proposal
    store.put(address, value)
    return address


def map_part(store, vertical, built, stubbed, next_, for_):
    address = f"px.exp.brain.map.{vertical}"
    store.put(
        address,
        {"for": for_, "built": list(built), "stubbed": list(stubbed), "next": list(next_)},
    )
    return address


def navigate(store):
    """what exists, by kind: the vertical's own PQL walk over the store."""
    out = {}
    for kind in ("data", "result", "oracle", "bench", "bracket", "map"):
        out[kind] = list(store.addresses(f"px.exp.brain.{kind}."))
    out["findings"] = list(store.addresses("proposal.brain."))
    oracles = [store.get(a) for a in out["oracle"]]
    out["oracles_passing"] = sum(1 for o in oracles if o.get("pass"))
    out["oracles_total"] = len(oracles)
    out["unjudged"] = [a for a in out["bracket"] if not store.get(a).get("judged")]
    return out
