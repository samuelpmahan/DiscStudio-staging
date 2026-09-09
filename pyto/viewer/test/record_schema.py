"""A Python validator for pyto-run-record@1, written from RECORD.md.

Why this file exists, and why it is not `from pyto.materialize import ...`:
the record is a contract between two runtimes, and a contract checked only by
the side that wrote it is not checked at all. `pyto/viewer/adapters.js`
validates in JavaScript what Python produced; this validates in Python what
JavaScript produced. The two implementations are deliberately independent --
this one is transcribed from `pyto/viewer/RECORD.md`, clause by clause, with
each rule naming the line of RECORD.md it comes from -- so a field one side
invents or omits fails on the other side instead of travelling unnoticed.

Strictness is the point. Key sets are exact in both directions:
  - a missing key is an error, because RECORD.md:65 says missing fields are
    null, never absent ("Missing fields are null, never invented");
  - an unknown key is an error, because a field neither RECORD.md nor the other
    runtime knows about is exactly the invention that clause forbids.

`validate(record)` returns the record unchanged or raises RecordSchemaError,
whose `.path` names the offending location the way adapters.js does
(`ticks[0].invocations[2].value.kind`), so a failure from either runtime reads
the same.
"""

from __future__ import annotations

import json

SCHEMA = "pyto-run-record@1"                     # RECORD.md:16
RUNTIMES = ("pyto", "discstudio", "chesslab", "wumpus")   # RECORD.md:18
VALUE_KINDS = ("json", "text", "svg", "png-data-url", "omitted")  # RECORD.md:59-63
WRITE_KINDS = ("new-address", "refinement", "replacement")
MAX_VALUE_BYTES = 262144                          # RECORD.md:63
MAX_ARRAY_ENTRIES = 200                           # RECORD.md:64

DOCUMENT_KEYS = ("schema", "pcr", "source", "ticks", "parts", "counters")
SOURCE_KEYS = ("runtime", "version", "commit")
TICK_KEYS = ("index", "name", "invocations")
INVOCATION_KEYS = (
    "id", "calculation", "inputs", "args", "into",
    "declared_consumes", "actual_consumes", "actual_produces", "writes",
    "duration_ms", "result_sha256", "hit", "value",
)
CALCULATION_KEYS = ("address", "implementation_sha256", "identity_scope")
WRITE_KEYS = ("address", "kind")
VALUE_KEYS = ("kind", "data", "note")
PART_KEYS = ("written_by", "read_by", "preexisting")
COUNTER_KEYS = ("invocations", "hits", "computed", "wall_ms")


class RecordSchemaError(ValueError):
    """A violation of RECORD.md, carrying the path that names it."""

    def __init__(self, path: str, message: str) -> None:
        super().__init__(f"{SCHEMA} {path}: {message}")
        self.path = path
        self.reason = message


def _fail(path, message):
    raise RecordSchemaError(path, message)


def _show(value):
    if isinstance(value, bool) or value is None or isinstance(value, (int, float, str)):
        return json.dumps(value)
    return type(value).__name__


def _keys(value, path, expected):
    """Exactly `expected`, in any order: nothing missing, nothing invented."""
    if not isinstance(value, dict):
        _fail(path, f"expected an object, got {_show(value)}")
    have, want = set(value), set(expected)
    missing, extra = sorted(want - have), sorted(have - want)
    if missing:
        _fail(path, f"missing required field(s) {', '.join(missing)}; RECORD.md: missing fields are null, never absent")
    if extra:
        _fail(path, f"unknown field(s) {', '.join(extra)} not in RECORD.md")
    return value


def _obj(value, path):
    if not isinstance(value, dict):
        _fail(path, f"expected an object, got {_show(value)}")
    return value


def _arr(value, path):
    if not isinstance(value, list):
        _fail(path, f"expected an array, got {_show(value)}")
    return value


def _str(value, path, non_empty=True):
    if not isinstance(value, str):
        _fail(path, f"expected a string, got {_show(value)}")
    if non_empty and not value:
        _fail(path, "expected a non-empty string")
    return value


def _nullable_str(value, path):
    if value is not None and not isinstance(value, str):
        _fail(path, f"expected a string or null, got {_show(value)}")
    return value


def _nullable_number(value, path):
    if value is None:
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(path, f"expected a number or null, got {_show(value)}")
    return value


def _bool(value, path):
    if not isinstance(value, bool):
        _fail(path, f"expected true or false, got {_show(value)}")
    return value


def _enum(value, allowed, path):
    if value not in allowed:
        _fail(path, f"expected one of {', '.join(json.dumps(a) for a in allowed)}, got {_show(value)}")
    return value


def _str_array(value, path):
    _arr(value, path)
    for i, entry in enumerate(value):
        _str(entry, f"{path}[{i}]", non_empty=False)
    return value


def _binding(value, path):
    """RECORD.md:52-53: inputs keep the testimony spelling, px: or fn:."""
    _str(value, path)
    if not value.startswith("px:") and not value.startswith("fn:"):
        _fail(path, f'expected a testimony binding spelled "px:<address>" or "fn:<id>", got {_show(value)}')
    return value


def _value(block, path):
    """RECORD.md:59-64."""
    _keys(block, path, VALUE_KEYS)
    kind = _enum(block["kind"], VALUE_KINDS, f"{path}.kind")
    _nullable_str(block["note"], f"{path}.note")
    data = block["data"]
    if kind == "omitted":
        if data is not None:
            _fail(f"{path}.data", f'expected null for kind "omitted", got {_show(data)}')
        if not isinstance(block["note"], str) or not block["note"]:
            _fail(f"{path}.note", 'kind "omitted" must say why in note')
    elif kind == "json":
        # any JSON value, including null -- json.load already proved that
        pass
    else:
        _str(data, f"{path}.data", non_empty=False)
    return block


def _invocation(inv, path, seen_ids):
    _keys(inv, path, INVOCATION_KEYS)
    ident = _str(inv["id"], f"{path}.id")
    if ident in seen_ids:
        _fail(f"{path}.id", f"duplicate invocation id {json.dumps(ident)}; ids anchor annotations and must be unique in a record")
    seen_ids.add(ident)

    calc = _keys(inv["calculation"], f"{path}.calculation", CALCULATION_KEYS)
    _nullable_str(calc["address"], f"{path}.calculation.address")
    _nullable_str(calc["implementation_sha256"], f"{path}.calculation.implementation_sha256")
    _str(calc["identity_scope"], f"{path}.calculation.identity_scope")

    for name, binding in _obj(inv["inputs"], f"{path}.inputs").items():
        _binding(binding, f"{path}.inputs.{name}")
    _obj(inv["args"], f"{path}.args")
    _nullable_str(inv["into"], f"{path}.into")

    for i, entry in enumerate(_arr(inv["declared_consumes"], f"{path}.declared_consumes")):
        _binding(entry, f"{path}.declared_consumes[{i}]")
    _str_array(inv["actual_consumes"], f"{path}.actual_consumes")
    _str_array(inv["actual_produces"], f"{path}.actual_produces")

    for i, write in enumerate(_arr(inv["writes"], f"{path}.writes")):
        wpath = f"{path}.writes[{i}]"
        _keys(write, wpath, WRITE_KEYS)
        _str(write["address"], f"{wpath}.address")
        if write["kind"] is not None:
            _enum(write["kind"], WRITE_KINDS, f"{wpath}.kind")

    _nullable_number(inv["duration_ms"], f"{path}.duration_ms")
    _nullable_str(inv["result_sha256"], f"{path}.result_sha256")
    _bool(inv["hit"], f"{path}.hit")
    _value(inv["value"], f"{path}.value")
    return inv


def validate(record):
    """Return `record` unchanged, or raise RecordSchemaError naming the path."""
    _keys(record, "document", DOCUMENT_KEYS)
    if record["schema"] != SCHEMA:
        _fail("schema", f"expected {json.dumps(SCHEMA)}, got {_show(record['schema'])}")
    _str(record["pcr"], "pcr")

    source = _keys(record["source"], "source", SOURCE_KEYS)
    _enum(source["runtime"], RUNTIMES, "source.runtime")
    _nullable_str(source["version"], "source.version")
    _nullable_str(source["commit"], "source.commit")

    ticks = _arr(record["ticks"], "ticks")
    seen_ids, n_invocations, n_hits = set(), 0, 0
    for index, tick in enumerate(ticks):
        path = f"ticks[{index}]"
        _keys(tick, path, TICK_KEYS)
        if tick["index"] != index or isinstance(tick["index"], bool):
            _fail(f"{path}.index", f"expected {index} (position in ticks), got {_show(tick['index'])}")
        _str(tick["name"], f"{path}.name")
        for i, inv in enumerate(_arr(tick["invocations"], f"{path}.invocations")):
            _invocation(inv, f"{path}.invocations[{i}]", seen_ids)
            n_invocations += 1
            if inv["hit"]:
                n_hits += 1

    for address, part in _obj(record["parts"], "parts").items():
        path = f'parts[{json.dumps(address)}]'
        _keys(part, path, PART_KEYS)
        _nullable_str(part["written_by"], f"{path}.written_by")
        _str_array(part["read_by"], f"{path}.read_by")
        _bool(part["preexisting"], f"{path}.preexisting")

    counters = _keys(record["counters"], "counters", COUNTER_KEYS)
    for key in ("invocations", "hits", "computed"):
        value = counters[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            _fail(f"counters.{key}", f"expected a non-negative integer, got {_show(value)}")
    _nullable_number(counters["wall_ms"], "counters.wall_ms")
    if counters["invocations"] != n_invocations:
        _fail("counters.invocations", f"expected {n_invocations} (invocations in ticks), got {counters['invocations']}")
    if counters["hits"] != n_hits:
        _fail("counters.hits", f"expected {n_hits} (invocations with hit=true), got {counters['hits']}")
    if counters["hits"] + counters["computed"] != counters["invocations"]:
        _fail("counters.computed", f"expected {counters['invocations'] - counters['hits']} so hits + computed === invocations, got {counters['computed']}")
    return record


def derive_part_index(ticks):
    """RECORD.md:66 -- parts is derived from the invocations, for convenience.

    Written from that clause and RECORD.md:52-57, independently of adapters.js
    `derivePartIndex` and of `pyto.materialize`, so the `parts` block is checked
    against a third reading of the rule instead of being trusted because two
    files by the same hand agree. `read_by` is compared sorted: RECORD.md fixes
    the membership, not the order.

    - a `px:` binding reads that address; a `fn:` binding reads the address the
      named invocation wrote (RECORD.md:52-53, and the example at :44 where the
      readers of scratch.ablation.split are the fit/score invocations);
    - `actual_consumes` are bare addresses already observed on the store;
    - an address read before anything in this run wrote it preexisted
      (RECORD.md:55-57, the same clause `hit` is built on).
    """
    index = {}
    produced_by = {}

    def entry(address):
        return index.setdefault(address, {"written_by": None, "read_by": [], "preexisting": False})

    for tick in ticks:
        for inv in tick["invocations"]:
            reads = []
            for binding in list(inv["inputs"].values()) + list(inv["declared_consumes"]):
                if binding.startswith("px:"):
                    reads.append(binding[3:])
                elif binding.startswith("fn:") and binding[3:] in produced_by:
                    reads.append(produced_by[binding[3:]])
            reads.extend(inv["actual_consumes"])
            for address in reads:
                item = entry(address)
                if item["written_by"] is None:
                    item["preexisting"] = True
                if inv["id"] not in item["read_by"]:
                    item["read_by"].append(inv["id"])

            writes = list(inv["actual_produces"]) + [w["address"] for w in inv["writes"]]
            if inv["into"]:
                writes.append(inv["into"])
                produced_by[inv["id"]] = inv["into"]
            for address in writes:
                item = entry(address)
                if item["written_by"] is None:
                    item["written_by"] = inv["id"]
    return index
