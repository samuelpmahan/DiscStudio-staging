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
  - a missing key is an error, because RECORD.md:114 says missing fields are
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

SCHEMA = "pyto-run-record@1"                     # RECORD.md:20
RUNTIMES = ("pyto", "discstudio", "chesslab", "wumpus")   # RECORD.md:22
VALUE_KINDS = ("json", "text", "svg", "png-data-url", "omitted")  # RECORD.md:108-112
WRITE_KINDS = ("new-address", "refinement", "replacement")
MAX_VALUE_BYTES = 262144                          # RECORD.md:112
MAX_ARRAY_ENTRIES = 200                           # RECORD.md:113
PNG_DATA_URL_PREFIX = "data:image/png;base64,"    # RECORD.md:109-110

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
    """RECORD.md: inputs keep the testimony spelling, `px:` or `fn:`.

    A result binding is `fn:<id>` or, when the producer published several Parts,
    `fn:<id>#<address>`; both halves of the qualified form must be non-empty, so
    a reader always has a producer to resolve and an address to resolve it to.
    """
    _str(value, path)
    if not value.startswith("px:") and not value.startswith("fn:"):
        _fail(path, f'expected a testimony binding spelled "px:<address>", "fn:<id>" or "fn:<id>#<address>", got {_show(value)}')
    if value.startswith("fn:") and "#" in value:
        writer, _, produce = value[3:].rpartition("#")
        if not writer or not produce:
            _fail(path, f'expected a produce-qualified result binding "fn:<id>#<address>", got {_show(value)}')
    return value


def _into(value, path):
    """RECORD.md: `into` is one address, an array of addresses, or null.

    The array is the multi-produce form: an invocation that published several
    Parts from one pass. An empty array is refused -- an invocation that produced
    nothing writes null, the way every other absent field does -- and so is a
    repeated address, which would claim one Part was published twice by one
    invocation.
    """
    if value is None or isinstance(value, str):
        return _nullable_str(value, path)
    if not isinstance(value, list):
        _fail(path, f"expected an address, an array of addresses, or null, got {_show(value)}")
    if not value:
        _fail(path, "expected at least one address; an invocation that produces nothing writes null")
    seen = set()
    for index, entry in enumerate(value):
        _str(entry, f"{path}[{index}]")
        if entry in seen:
            _fail(f"{path}[{index}]", f"duplicate produce address {json.dumps(entry)}; one invocation publishes each address once")
        seen.add(entry)
    return value


def produce_addresses(into):
    """The addresses an invocation's `into` names: none, one, or several."""
    if into is None:
        return ()
    return (into,) if isinstance(into, str) else tuple(into)


def resolve_binding(binding, produced_by):
    """The Part addresses one testimony binding reads (RECORD.md, Field rules).

    `px:<address>` is that address. `fn:<id>` is the whole result of that
    invocation, which is the one Part it published; `fn:<id>#<address>` names one
    produce of an invocation that published several. A known id wins over the `#`
    split, so an invocation id carrying a `#` still resolves as the bare reference
    it is. `produced_by` maps an invocation id to the addresses it published.
    """
    if binding.startswith("px:"):
        return (binding[3:],)
    if not binding.startswith("fn:"):
        return ()
    body = binding[3:]
    if body in produced_by:
        return tuple(produced_by[body])
    writer, separator, address = body.rpartition("#")
    if separator and address and address in produced_by.get(writer, ()):
        return (address,)
    return ()


def _value(block, path):
    """RECORD.md:108-113."""
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
        # RECORD.md:109-110 does not merely name the kind, it states the shape:
        # "data is a `data:image/png;base64,...` string". A viewer puts this
        # string into an <img src>, so the clause is checked, not assumed.
        if kind == "png-data-url" and not data.startswith(PNG_DATA_URL_PREFIX):
            _fail(
                f"{path}.data",
                f'expected a string beginning "{PNG_DATA_URL_PREFIX}" for kind "png-data-url", got {_show(data)}',
            )
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
    _into(inv["into"], f"{path}.into")

    # RECORD.md's declared_consumes rule is strict, so it is checked and not
    # assumed: exactly the `px:` bindings of `inputs`, in binding order. An
    # `fn:` entry or an address `inputs` does not carry would add a read edge no
    # binding declares, because derive_part_index below unions the two fields.
    bound_values = set(inv["inputs"].values())
    for i, entry in enumerate(_arr(inv["declared_consumes"], f"{path}.declared_consumes")):
        where = f"{path}.declared_consumes[{i}]"
        _binding(entry, where)
        if not entry.startswith("px:"):
            _fail(where, f'declared_consumes carries Part bindings only, spelled "px:<address>", got {_show(entry)}')
        if entry not in bound_values:
            _fail(where, f"declared_consumes is a subset of inputs.values(), which does not carry {_show(entry)}")
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
    """RECORD.md:115 -- parts is derived from the invocations, for convenience.

    Written from that clause and RECORD.md:80-107, independently of adapters.js
    `derivePartIndex` and of `pyto.materialize`, so the `parts` block is checked
    against a third reading of the rule instead of being trusted because two
    files by the same hand agree. `read_by` is compared sorted: RECORD.md fixes
    the membership, not the order.

    - a `px:` binding reads that address; a `fn:` binding reads the address the
      named invocation wrote (RECORD.md:80-82, and the example at :71 where the
      readers of scratch.ablation.split are the fit/score invocations), and
      `fn:<id>#<address>` reads the one produce it names (`resolve_binding`);
    - `actual_consumes` are bare addresses already observed on the store;
    - an address read before anything in this run wrote it preexisted
      (RECORD.md:104-107, the same clause `hit` is built on).
    """
    index = {}
    produced_by = {}

    def entry(address):
        return index.setdefault(address, {"written_by": None, "read_by": [], "preexisting": False})

    for tick in ticks:
        for inv in tick["invocations"]:
            reads = []
            for binding in list(inv["inputs"].values()) + list(inv["declared_consumes"]):
                reads.extend(resolve_binding(binding, produced_by))
            reads.extend(inv["actual_consumes"])
            for address in reads:
                item = entry(address)
                if item["written_by"] is None:
                    item["preexisting"] = True
                if inv["id"] not in item["read_by"]:
                    item["read_by"].append(inv["id"])

            writes = list(inv["actual_produces"]) + [w["address"] for w in inv["writes"]]
            produces = produce_addresses(inv["into"])
            if produces:
                writes.extend(produces)
                produced_by[inv["id"]] = produces
            for address in writes:
                item = entry(address)
                if item["written_by"] is None:
                    item["written_by"] = inv["id"]
    return index
