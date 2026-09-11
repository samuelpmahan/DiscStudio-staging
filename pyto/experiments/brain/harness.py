"""the shared harness for the pxc brain: parts in, parts out.

every vertical (backend, stats, ml, data) builds against this one file. it owns
the address scheme written down in CONTRACT.md and nothing else: a `Store` over
`PxC` that persists itself as json, the evidence parts (dataset, synthetic,
oracle, benchmark, bracket), the finding and map parts, and `navigate` which
reads all of it back through `PQL`. it never decides what a vertical computes.

everything here is lowercase and carries its `for`. nothing here promotes
anything: the whole brain lives under `px.exp.brain.*` and `proposal.brain.*`.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import atexit
import shutil
import statistics
import tempfile
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

from pyto import PCR, PQL, Part, PxC
from pyto.materialize import run_record, write_record

BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))
STORE_DIR = os.path.join(BRAIN_DIR, "store")
RECORDS_DIR = os.path.join(BRAIN_DIR, "records")

# A run record holds wall-clock durations and a benchmark Part holds wall_ms, so anything
# that writes one into a tracked path rewrites it on every suite run: MAIN goes dirty, and
# `land.sh` refuses to land into a dirty tree. So a `Store` writes into a temporary
# directory unless it is told otherwise, and only an explicit record run - `Store(commit=True)`
# or `BRAIN_RECORDS=commit python -m ...` - writes the committed store and records.
# Reading is not affected: `load_store()` reads the committed `store/` either way.
COMMIT_ENV = "BRAIN_RECORDS"


def committing(flag: bool | None = None) -> bool:
    """whether writes land in the repository. a flag wins; otherwise the environment."""
    if flag is not None:
        return bool(flag)
    return os.environ.get(COMMIT_ENV, "").strip().lower() == "commit"

PX = "px.exp.brain."
DATA = PX + "data."
RESULT = PX + "result."
ORACLE = PX + "oracle."
BENCH = PX + "bench."
BRACKET = PX + "bracket."
MAP = PX + "map."
FINDING = "proposal.brain."

KINDS = ("data", "result", "oracle", "bench", "bracket", "map")
DEFAULT_TOLERANCE = 1e-9
# An oracle Part is evidence, and a 192x192 matrix of distances is 1.4 MB of decimal text in it -
# four candidates at three sizes was 6.5 MB of store before this cap. A value a reader could
# plausibly read is kept whole; past that, what is kept is what a reader can actually check (how
# big it is, what it digests to, its shape, where it starts). The comparison itself always runs on
# the full value, never on the outline.
ORACLE_VALUE_CAP = 65536


# --- addresses -----------------------------------------------------------------


def token(text: str, what: str = "name") -> str:
    """one lowercase address segment. the sprint's one style rule, enforced."""
    text = str(text)
    if not text:
        raise ValueError(f"brain: {what} must be non-empty")
    if text != text.lower():
        raise ValueError(f"brain: {what} {text!r} must be lowercase (the sprint's one style rule)")
    if "." in text or " " in text:
        raise ValueError(f"brain: {what} {text!r} must be one address segment (no dots, no spaces)")
    return text


def result_address(vertical: str, calc: str, case: str) -> str:
    return f"{RESULT}{token(vertical)}.{token(calc)}.{token(case)}"


def oracle_address(vertical: str, calc: str, case: str) -> str:
    return f"{ORACLE}{token(vertical)}.{token(calc)}.{token(case)}"


def bench_address(vertical: str, calc: str, backend: str, size: Any) -> str:
    return f"{BENCH}{token(vertical)}.{token(calc)}.{token(backend)}.{token(size, 'size')}"


def bracket_address(vertical: str, problem: str) -> str:
    return f"{BRACKET}{token(vertical)}.{token(problem)}"


def map_address(vertical: str) -> str:
    return f"{MAP}{token(vertical)}"


def finding_address(vertical: str, k: str) -> str:
    return f"{FINDING}{token(vertical)}.{token(k)}"


def data_address(name: str) -> str:
    return f"{DATA}{token(name)}"


# --- json ----------------------------------------------------------------------


def jsonable(value: Any) -> Any:
    """every part value in the brain is json, so records and digests work.

    numpy scalars and arrays are converted here rather than at a hundred call
    sites; anything else that json cannot hold is refused loudly, naming itself.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): jsonable(inner) for key, inner in value.items()}
    if hasattr(value, "tolist") and hasattr(value, "shape"):  # numpy array or scalar
        return jsonable(value.tolist())
    if hasattr(value, "item") and hasattr(value, "dtype"):  # numpy scalar
        return jsonable(value.item())
    if isinstance(value, (list, tuple, set, frozenset)):
        return [jsonable(inner) for inner in value]
    raise TypeError(
        f"brain: {type(value).__name__} is not json-able; every part value must be "
        "(the store is persisted as json and digested as json)"
    )


def shape_of(value: Any) -> list[int]:
    """the dimensions of a nested list, as far as it is rectangular."""
    dims = []
    while isinstance(value, (list, tuple)):
        dims.append(len(value))
        value = value[0] if value else None
    return dims


def outline(value: Any, cap: int = ORACLE_VALUE_CAP) -> Any:
    """`value` if it is small; otherwise the same shape with its big parts outlined.

    a mapping keeps its keys - `{"shape": [192, 192]}` stays readable and only its
    `values` is replaced - and a long sequence becomes how long it is, what it
    digests to, and the numbers it starts with. nothing that reads a Part has to
    know which it got: `outline` is true on the ones that were replaced.
    """
    plain = jsonable(value)
    text = json.dumps(plain, separators=(",", ":"), default=str)
    if len(text) <= cap:
        return plain
    if isinstance(plain, dict):
        return {key: outline(inner, cap) for key, inner in plain.items()}
    flat: list[Any] = []

    def walk(node):
        if len(flat) >= 8:
            return
        if isinstance(node, list):
            for one in node:
                walk(one)
        else:
            flat.append(node)

    walk(plain)
    return {"outline": True, "json_bytes": len(text), "sha256": digest(plain), "shape": shape_of(plain), "head": flat}


def digest(value: Any) -> str:
    """sha256 of a value's canonical json. the same value digests the same way."""
    text = json.dumps(jsonable(value), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- the store -----------------------------------------------------------------


class Ref:
    """bind an input to an earlier step's result rather than to a store part.

    binding by address is usually enough (`PCR` rewrites a read of a part this
    same program writes into a read of the writer's result); `Ref` is for the
    case where the same address is written twice or the binding should be
    explicit in the program text.
    """

    __slots__ = ("id", "address")

    def __init__(self, step_id: str, address: str | None = None) -> None:
        self.id = step_id
        self.address = address

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Ref({self.id!r}, {self.address!r})"


class Store:
    """`PxC` with the brain's manners: json parts, a file per vertical, records.

    `put`/`get` are the store; `run` is the only way a calculation runs (a `PCR`
    observed, its record written under `records/`); `save`/`load_store` are how a
    vertical's parts outlive the process and how the map sees every vertical.
    """

    def __init__(
        self,
        pxc: PxC | None = None,
        store_dir: str | None = None,
        records_dir: str | None = None,
        commit: bool | None = None,
    ) -> None:
        self.pxc = pxc if pxc is not None else PxC()
        self.read_store_dir = store_dir or STORE_DIR
        self.commit = committing(commit)
        if store_dir or records_dir or self.commit:
            self.scratch = None
            self.store_dir = store_dir or STORE_DIR
            self.records_dir = records_dir or RECORDS_DIR
        else:
            # the default: read the committed store, write nothing the repository tracks.
            # mkdtemp plus atexit rather than TemporaryDirectory, so a Store that is simply
            # dropped does not warn about an implicit cleanup in the middle of a suite.
            self.scratch = tempfile.mkdtemp(prefix="brain-scratch-")
            atexit.register(shutil.rmtree, self.scratch, True)
            self.store_dir = os.path.join(self.scratch, "store")
            self.records_dir = os.path.join(self.scratch, "records")
        self.written: list[str] = []
        self.loaded: dict[str, int] = {}
        self.records: list[str] = []

    @property
    def writes_into_the_repository(self) -> bool:
        """true only for an explicit record run: `Store(commit=True)` or BRAIN_RECORDS=commit."""
        return os.path.abspath(self.records_dir).startswith(os.path.abspath(BRAIN_DIR))

    # -- parts
    def put(self, address: Any, value: Any) -> str:
        address = str(address)
        if address != address.lower():
            raise ValueError(f"brain: address {address!r} must be lowercase")
        if not (address.startswith(PX) or address.startswith(FINDING)):
            raise ValueError(
                f"brain: address {address!r} is outside the brain "
                f"(a part is {PX}* or {FINDING}*)"
            )
        self.pxc.set(Part(address), jsonable(value))
        if address not in self.written:
            self.written.append(address)
        return address

    def get(self, address: Any) -> Any:
        return self.pxc.get(str(address))

    def has(self, address: Any) -> bool:
        return self.pxc.has(str(address))

    def addresses(self) -> tuple[str, ...]:
        return self.pxc.addresses()

    def brain_addresses(self) -> tuple[str, ...]:
        return tuple(a for a in self.pxc.addresses() if a.startswith(PX) or a.startswith(FINDING))

    # -- persistence
    def save(self, vertical: str, path: str | None = None) -> str:
        """persist this process's brain parts to `<store_dir>/<vertical>.json`.

        what a vertical wrote this process is merged over whatever the file
        already held, so a second run adds to the store instead of truncating it.
        `store_dir` is the repository's `store/` only for an explicit record run
        (`Store(commit=True)`, or `BRAIN_RECORDS=commit`); by default it is a
        temporary directory, so a test can save a store without dirtying MAIN.
        The path it wrote is returned - read it rather than assuming.
        """
        vertical = token(vertical, "vertical")
        path = path or os.path.join(self.store_dir, f"{vertical}.json")
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        held: dict[str, Any] = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as handle:
                held = json.load(handle)
        for address in self.written:
            if self.pxc.has(address):
                held[address] = jsonable(self.pxc.get(address))
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(held, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return path

    def load_store(self, store_dir: str | None = None) -> dict[str, int]:
        """merge every `store/*.json` into this store. how a vertical sees the rest.

        reading is always from the committed `store/` (or from an explicit
        `store_dir`): only writing defaults to a temporary directory.
        """
        directory = store_dir or self.read_store_dir
        loaded: dict[str, int] = {}
        if not os.path.isdir(directory):
            self.loaded = loaded
            return loaded
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(directory, name)
            with open(path, encoding="utf-8") as handle:
                parts = json.load(handle)
            for address, value in parts.items():
                self.pxc.set(Part(address), value)
            loaded[name] = len(parts)
        self.loaded = loaded
        return loaded

    # -- running
    def run(self, name: str, ticks: Sequence[tuple[str, Sequence[Mapping[str, Any]]]], record_name: str | None = None):
        """build one `PCR` from `ticks`, run it observed, write its record.

        `ticks` is a sequence of `(tick_name, steps)`; a step is a mapping with
        `calc` (a `Calculation`), `id`, `into` (one address or a list), optional
        `args` and optional `inputs` (name -> address or `Ref`). returns the
        `PcrRun`, which carries `results`, `ticks` (the testimony) and, because
        every brain run is observed, one `Receipt` per id.
        """
        name = token(name, "pcr name")
        pcr = PCR(name)
        refs: dict[str, Any] = {}
        produced: list[str] = []
        for tick_name, steps in ticks:
            for step in steps:
                calc = step["calc"]
                step_id = step["id"]
                into = step["into"]
                if isinstance(into, str):
                    into_arg: Any = Part(into)
                    produced.append(into)
                else:
                    into_arg = [Part(str(one)) for one in into]
                    produced.extend(str(one) for one in into)
                bindings = {}
                for key, source in dict(step.get("inputs", {})).items():
                    if isinstance(source, Ref):
                        ref = refs[source.id]
                        bindings[key] = ref if source.address is None else ref[Part(source.address)]
                    elif isinstance(source, str):
                        bindings[key] = Part(source)
                    else:
                        bindings[key] = source
                refs[step_id] = pcr.calc(
                    tick_name, calc, id=step_id, into=into_arg, args=dict(step.get("args", {})), **bindings
                )
        preexisting = set(self.pxc.addresses())
        run = pcr.run(self.pxc, observe=True)
        record = run_record(run, self.pxc, preexisting=preexisting)
        os.makedirs(self.records_dir, exist_ok=True)
        path = os.path.join(self.records_dir, f"{record_name or name}.json")
        write_record(record, path)
        self.records.append(path)
        for address in produced:
            if (address.startswith(PX) or address.startswith(FINDING)) and address not in self.written:
                self.written.append(address)
        return run

    # -- the helpers, spelled as methods too, so `store.oracle(...)` reads like the contract
    def dataset(self, *a, **k):
        return dataset(self, *a, **k)

    def synthetic(self, *a, **k):
        return synthetic(self, *a, **k)

    def oracle(self, *a, **k):
        return oracle(self, *a, **k)

    def bench(self, *a, **k):
        return bench(self, *a, **k)

    def bracket(self, *a, **k):
        return bracket(self, *a, **k)

    def judge(self, *a, **k):
        return judge(self, *a, **k)

    def decide(self, *a, **k):
        return decide(self, *a, **k)

    def refine(self, *a, **k):
        return refine(self, *a, **k)

    def finding(self, *a, **k):
        return finding(self, *a, **k)

    def map_part(self, *a, **k):
        return map_part(self, *a, **k)

    def navigate(self):
        return navigate(self)


# --- datasets ------------------------------------------------------------------


def dataset(store: Store, name: str, for_: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """a table as one part: `{for, columns, rows}` at `px.exp.brain.data.<name>`."""
    address = data_address(name)
    rows = [list(row) for row in rows]
    for row in rows:
        if len(row) != len(columns):
            raise ValueError(f"brain: dataset {name!r} row has {len(row)} cells for {len(columns)} columns")
    store.put(address, {"for": for_, "columns": list(columns), "rows": rows})
    return address


def synthetic(store: Store, name: str, for_: str, seed: int, shape: Sequence[int], kind: str = "normal") -> str:
    """a drawn matrix as one part: `{for, shape, values, seed, kind}`.

    the seed is an argument and the draw is numpy's generator inside a pure
    function of it, so the same seed is the same part everywhere, every time.
    """
    import numpy as np

    kind = token(kind, "kind")
    shape = tuple(int(one) for one in shape)
    rng = np.random.default_rng(int(seed))
    if kind == "normal":
        values = rng.standard_normal(shape)
    elif kind == "uniform":
        values = rng.random(shape)
    elif kind == "integers":
        values = rng.integers(0, 100, shape)
    elif kind == "spd":
        if len(shape) != 2 or shape[0] != shape[1]:
            raise ValueError("brain: kind 'spd' needs a square shape")
        base = rng.standard_normal(shape)
        values = base @ base.T + shape[0] * np.eye(shape[0])
    elif kind == "sorted":
        values = np.sort(rng.standard_normal(shape), axis=-1)
    else:
        raise ValueError(f"brain: unknown synthetic kind {kind!r} (normal, uniform, integers, spd, sorted)")
    address = data_address(name)
    store.put(
        address,
        {"for": for_, "shape": list(shape), "values": values.tolist(), "seed": int(seed), "kind": kind},
    )
    return address


def values_of(part: Mapping[str, Any]) -> list:
    """the numbers in a dataset part, whichever of the two shapes it has."""
    if "values" in part:
        return part["values"]
    return part["rows"]


# --- oracles -------------------------------------------------------------------


def close(got: Any, expected: Any, tolerance: float = DEFAULT_TOLERANCE) -> tuple[bool, float]:
    """(pass, worst relative error) over two json-able structures of numbers."""
    worst = 0.0

    def walk(a: Any, b: Any) -> bool:
        nonlocal worst
        if isinstance(a, Mapping) or isinstance(b, Mapping):
            if not (isinstance(a, Mapping) and isinstance(b, Mapping)) or set(a) != set(b):
                return False
            return all(walk(a[key], b[key]) for key in sorted(a))
        if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
            if not (isinstance(a, (list, tuple)) and isinstance(b, (list, tuple))) or len(a) != len(b):
                return False
            return all(walk(x, y) for x, y in zip(a, b))
        if isinstance(a, bool) or isinstance(b, bool) or isinstance(a, str) or isinstance(b, str) or a is None or b is None:
            return a == b
        a, b = float(a), float(b)
        if math.isnan(a) or math.isnan(b):
            return math.isnan(a) and math.isnan(b)
        if math.isinf(a) or math.isinf(b):
            return a == b
        error = abs(a - b) / max(1.0, abs(b))
        worst = max(worst, error)
        return error <= tolerance

    return walk(jsonable(got), jsonable(expected)), worst


def oracle(
    store: Store,
    vertical: str,
    calc: str,
    case: str,
    got: Any,
    expected: Any,
    reference: str,
    tolerance: float = DEFAULT_TOLERANCE,
    for_: str = "",
) -> bool:
    """one backend's answer against the reference, as a part. returns the verdict.

    a backend that changes semantics is a failed backend: this is where that is
    decided, and the failing part stays in the store as the evidence. the verdict
    is decided on the full values; what the Part keeps is `outline` of each, so a
    store stays a store and not a copy of every matrix anyone ever compared.
    """
    passed, worst = close(got, expected, tolerance)
    store.put(
        oracle_address(vertical, calc, case),
        {
            "for": for_,
            "calc": calc,
            "case": case,
            "reference": reference,
            "expected": outline(expected),
            "got": outline(got),
            "tolerance": tolerance,
            "worst_relative_error": worst,
            "pass": bool(passed),
        },
    )
    return bool(passed)


# --- benchmarks ----------------------------------------------------------------


def bench(
    store: Store,
    vertical: str,
    calc: str,
    backend: str,
    size: Any,
    fn: Callable[[], Any],
    n: int = 7,
    for_: str = "",
    inputs: Any = None,
) -> dict:
    """n wall-clock runs of `fn`, median and min, as a part.

    `time.perf_counter` is allowed HERE, in the host that measures, and never
    inside a `Calculation` (a calculation that needs a clock is `oc.` and takes
    it through the effects handle).
    """
    if n < 1:
        raise ValueError("brain: bench needs n >= 1")
    samples = []
    for _ in range(int(n)):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    value = {
        "for": for_,
        "backend": token(backend, "backend"),
        "calc": calc,
        "size": str(size),
        "n": int(n),
        "wall_ms_median": statistics.median(samples),
        "wall_ms_min": min(samples),
        "inputs_sha256": digest(inputs if inputs is not None else {"calc": calc, "size": str(size)}),
    }
    store.put(bench_address(vertical, calc, backend, size), value)
    return value


# --- tournaments ---------------------------------------------------------------


def _criterion(raw: Any) -> dict:
    if isinstance(raw, str):
        return {"name": token(raw, "criterion"), "how": "", "direction": "higher", "weight": 1.0}
    named = dict(raw)
    return {
        "name": token(named["name"], "criterion"),
        "how": named.get("how", ""),
        "direction": named.get("direction", "higher"),
        "weight": float(named.get("weight", 1.0)),
    }


def bracket(store: Store, vertical: str, problem: str, criteria: Sequence[Any], candidates: Sequence[Mapping[str, Any]], for_: str = "") -> str:
    """open a tournament: the criteria are written down BEFORE anyone judges.

    that ordering is the whole point, so `judge` refuses a bracket with no
    criteria and `decide` scores only by the criteria this part recorded.
    """
    if not criteria:
        raise ValueError("brain: a bracket records its criteria before any judging; this one has none")
    if len(candidates) < 2:
        raise ValueError("brain: a bracket needs at least two candidates")
    address = bracket_address(vertical, problem)
    store.put(
        address,
        {
            "for": for_,
            "problem": problem,
            "criteria": [_criterion(one) for one in criteria],
            "candidates": [
                {"branch": one["branch"], "calc": one.get("calc", ""), "address": one.get("address", ""), "note": one.get("note", "")}
                for one in candidates
            ],
            "judged": [],
            "winner": None,
            "refined": False,
        },
    )
    return address


def judge(store: Store, vertical: str, problem: str, judge: str, candidate: str, scores: Mapping[str, float], note: str = "") -> dict:
    """one judgment appended to the bracket. a judge that built a candidate is refused."""
    address = bracket_address(vertical, problem)
    part = dict(store.get(address))
    if not part.get("criteria"):
        raise ValueError(f"brain: bracket {problem!r} has no criteria; nothing may be judged yet")
    branches = [one["branch"] for one in part["candidates"]]
    if candidate not in branches:
        raise ValueError(f"brain: {candidate!r} is not a candidate in bracket {problem!r} ({branches})")
    if judge in branches:
        raise ValueError(f"brain: {judge!r} built a candidate in {problem!r}; a judge did not build")
    unknown = set(scores) - {one["name"] for one in part["criteria"]}
    if unknown:
        raise ValueError(f"brain: bracket {problem!r} has no criteria named {sorted(unknown)}")
    entry = {"judge": judge, "candidate": candidate, "scores": {k: float(v) for k, v in scores.items()}, "note": note}
    part["judged"] = [one for one in part["judged"] if not (one["judge"] == judge and one["candidate"] == candidate)]
    part["judged"].append(entry)
    store.put(address, part)
    return entry


def decide(store: Store, vertical: str, problem: str) -> dict:
    """the winner from the recorded scores, by the recorded criteria.

    each criterion is averaged over the judges, pointed the way the criterion
    says (higher or lower is better), min-max normalised across candidates so no
    one criterion's units decide the bracket, then weighted and summed.
    """
    address = bracket_address(vertical, problem)
    part = dict(store.get(address))
    criteria = part["criteria"]
    branches = [one["branch"] for one in part["candidates"]]
    judged = part["judged"]
    unjudged = [branch for branch in branches if not any(one["candidate"] == branch for one in judged)]
    if unjudged:
        raise ValueError(f"brain: bracket {problem!r} cannot be decided; unjudged: {unjudged}")
    means: dict[str, dict[str, float]] = {}
    for criterion in criteria:
        name = criterion["name"]
        means[name] = {}
        for branch in branches:
            values = [one["scores"][name] for one in judged if one["candidate"] == branch and name in one["scores"]]
            means[name][branch] = statistics.mean(values) if values else 0.0
    totals = {branch: 0.0 for branch in branches}
    for criterion in criteria:
        name, weight = criterion["name"], criterion["weight"]
        row = means[name]
        low, high = min(row.values()), max(row.values())
        for branch in branches:
            if high == low:
                normal = 1.0
            elif criterion["direction"] == "lower":
                normal = (high - row[branch]) / (high - low)
            else:
                normal = (row[branch] - low) / (high - low)
            totals[branch] += weight * normal
    best = max(sorted(branches), key=lambda branch: totals[branch])
    part["totals"] = totals
    part["means"] = means
    part["winner"] = best
    store.put(address, part)
    return part


def refine(store: Store, vertical: str, problem: str, note: str, address: str = "") -> dict:
    """the winner was taken further. recorded on the bracket; losers are kept."""
    bracket_at = bracket_address(vertical, problem)
    part = dict(store.get(bracket_at))
    if not part.get("winner"):
        raise ValueError(f"brain: bracket {problem!r} has no winner to refine")
    part["refined"] = True
    part["refinement"] = {"note": note, "address": address}
    store.put(bracket_at, part)
    return part


# --- findings and the map ------------------------------------------------------


def finding(store: Store, vertical: str, k: str, kind: str, text: str, for_: str, workaround: str | None = None, proposal: str | None = None) -> str:
    """a finding is a part, not a prose page. `strength` or `friction`, with its `for`."""
    if kind not in ("strength", "friction"):
        raise ValueError("brain: a finding is a 'strength' or a 'friction'")
    address = finding_address(vertical, k)
    value = {"for": for_, "kind": kind, "text": text}
    if workaround:
        value["workaround"] = workaround
    if proposal:
        value["proposal"] = proposal
    store.put(address, value)
    return address


def map_part(store: Store, vertical: str, built: Sequence[str], stubbed: Sequence[Mapping[str, str]], next_: Sequence[Mapping[str, str]], for_: str) -> str:
    """the vertical's territory: what is built, what is stubbed and why, what is next and for whom."""
    address = map_address(vertical)
    store.put(
        address,
        {
            "for": for_,
            "built": list(built),
            "stubbed": [{"address": one["address"], "why": one["why"]} for one in stubbed],
            "next": [{"what": one["what"], "for": one["for"]} for one in next_],
        },
    )
    return address


# --- navigation ----------------------------------------------------------------


def _kind_and_vertical(address: str) -> tuple[str, str]:
    rest = address[len(PX):]
    head, _, tail = rest.partition(".")
    if head == "data":
        return "data", "data"
    return head, (tail.split(".")[0] if tail else "")


def navigate(store: Store) -> dict:
    """pql over `px.exp.brain.*` and `proposal.brain.*`: the whole territory, read back.

    what exists (by kind and by vertical), which oracles failed, what won, what
    is still unjudged, what is stubbed, and every finding.
    """
    pxc = store.pxc
    brain = PQL.prefix(PX)
    proposals = PQL.prefix(FINDING)

    counts: dict[str, dict[str, int]] = {}
    for address in brain.addresses(pxc):
        kind, vertical = _kind_and_vertical(address)
        counts.setdefault(kind, {}).setdefault(vertical, 0)
        counts[kind][vertical] += 1

    oracles = [{"address": m.address, "pass": bool(m.value.get("pass")), "reference": m.value.get("reference", "")} for m in PQL.prefix(ORACLE).matches(pxc)]
    benches = [
        {"address": m.address, "backend": m.value.get("backend"), "size": m.value.get("size"), "wall_ms_median": m.value.get("wall_ms_median")}
        for m in PQL.prefix(BENCH).matches(pxc)
    ]
    brackets = PQL.prefix(BRACKET).matches(pxc)
    won = [
        {"address": m.address, "problem": m.value.get("problem"), "winner": m.value["winner"], "refined": bool(m.value.get("refined"))}
        for m in brackets
        if m.value.get("winner")
    ]
    unjudged = [
        {"address": m.address, "problem": m.value.get("problem"), "candidates": [c["branch"] for c in m.value.get("candidates", [])]}
        for m in brackets
        if not m.value.get("winner")
    ]
    stubbed = [
        {"vertical": m.address[len(MAP):], **one}
        for m in PQL.prefix(MAP).matches(pxc)
        for one in m.value.get("stubbed", [])
    ]
    next_ = [
        {"vertical": m.address[len(MAP):], **one}
        for m in PQL.prefix(MAP).matches(pxc)
        for one in m.value.get("next", [])
    ]
    findings = [
        {"address": m.address, "kind": m.value.get("kind"), "text": m.value.get("text"), "for": m.value.get("for")}
        for m in proposals.matches(pxc)
    ]
    return {
        "addresses": len(brain.addresses(pxc)) + len(proposals.addresses(pxc)),
        "counts": counts,
        "oracles": {"total": len(oracles), "failed": [one for one in oracles if not one["pass"]]},
        "benches": benches,
        "won": won,
        "unjudged": unjudged,
        "stubbed": stubbed,
        "next": next_,
        "findings": findings,
        "loaded": dict(store.loaded),
    }


def territory(store: Store) -> str:
    """`navigate` as the page `python -m experiments.brain.map` prints."""
    seen = navigate(store)
    lines = ["the pxc brain, read back through pql", ""]
    lines.append(f"parts: {seen['addresses']}   (stores loaded: {seen['loaded'] or 'none'})")
    for kind in KINDS:
        row = seen["counts"].get(kind)
        if row:
            inner = ", ".join(f"{vertical}={count}" for vertical, count in sorted(row.items()))
            lines.append(f"  {kind:9} {inner}")
    lines.append("")
    lines.append(f"oracles: {seen['oracles']['total']} ({len(seen['oracles']['failed'])} failed)")
    for one in seen["oracles"]["failed"]:
        lines.append(f"  FAILED {one['address']} against {one['reference']}")
    lines.append(f"benchmarks: {len(seen['benches'])}")
    lines.append("")
    lines.append("brackets")
    for one in seen["won"]:
        lines.append(f"  won      {one['problem']}: {one['winner']}" + ("  (refined)" if one["refined"] else ""))
    for one in seen["unjudged"]:
        lines.append(f"  unjudged {one['problem']}: {', '.join(one['candidates'])}")
    lines.append("")
    lines.append("stubbed")
    for one in seen["stubbed"]:
        lines.append(f"  {one['vertical']}: {one['address']} - {one['why']}")
    lines.append("")
    lines.append("next")
    for one in seen["next"]:
        lines.append(f"  {one['vertical']}: {one['what']}  (for {one['for']})")
    lines.append("")
    lines.append("findings")
    for one in seen["findings"]:
        lines.append(f"  {one['kind']:8} {one['address']}: {one['text']}")
    return "\n".join(lines)
