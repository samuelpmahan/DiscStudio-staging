"""the dataset Parts this vertical reads, and the loader that reads one from disk.

the built-in tables are written out here in full so that a Part is a fact, not a
draw: the same bytes every process, every machine. they carry missing cells,
repeated keys, mixed types and a long/wide pair on purpose, because that is what
the dataframe calculations have to survive.

``oc.brain.data.load`` is the one loader, and it is an ``oc.`` because reading a
file is an effect: it goes through the run's effects handle
(``args["effects"].read_text``), so the bytes it read land on the ledger and a
replay re-reads nothing.
"""

import json

from pyto import Calculation

from data.table import check, make

ORDERS = make(
    "a small orders table: repeated customers, a categorical region, a price with holes in it",
    ["order", "customer", "region", "items", "price", "expedited"],
    [
        [1001, "ada", "north", 3, 42.50, True],
        [1002, "bo", "south", 1, 19.99, False],
        [1003, "ada", "north", 7, None, False],
        [1004, "cy", "east", 2, 78.00, True],
        [1005, "bo", "south", 4, 33.25, False],
        [1006, "ada", "west", 1, 12.00, None],
        [1007, "dee", "east", 9, 155.75, True],
        [1008, "cy", "east", 3, 61.40, False],
        [1009, "dee", "north", 2, None, True],
        [1010, "bo", "west", 6, 88.10, False],
        [1011, "ada", "south", 5, 47.35, False],
        [1012, "eli", "north", 1, 9.99, True],
    ],
)

CUSTOMERS = make(
    "the customer side of a join: one row per customer, and one customer nobody ordered for",
    ["customer", "tier", "since"],
    [
        ["ada", "gold", 2019],
        ["bo", "silver", 2021],
        ["cy", "gold", 2020],
        ["dee", "bronze", 2023],
        ["fay", "silver", 2022],
    ],
)

READINGS = make(
    "a long sensor table to fold wide: station by month, with a gap",
    ["station", "month", "celsius"],
    [
        ["alpha", "jan", -3.2], ["alpha", "feb", -1.1], ["alpha", "mar", 4.8],
        ["beta", "jan", 2.5], ["beta", "feb", 3.9], ["beta", "mar", 9.1],
        ["gamma", "jan", 11.0], ["gamma", "mar", 18.4],
        ["alpha", "jan", -2.8], ["beta", "mar", 8.7],
    ],
)

GAPPY = make(
    "a column with holes at the front, the middle and the end, for the missing strategies",
    ["step", "reading", "label"],
    [
        [0, None, "a"],
        [1, 12.0, "a"],
        [2, None, None],
        [3, 16.0, "b"],
        [4, 20.0, "b"],
        [5, None, "c"],
        [6, None, None],
    ],
)

BUILT_IN = {
    "orders": ORDERS,
    "customers": CUSTOMERS,
    "readings": READINGS,
    "gappy": GAPPY,
}


def _sniff(text, delimiter=","):
    rows = []
    field = ""
    row = []
    quoted = False
    index = 0
    while index < len(text):
        char = text[index]
        if quoted:
            if char == '"':
                if index + 1 < len(text) and text[index + 1] == '"':
                    field += '"'
                    index += 1
                else:
                    quoted = False
            else:
                field += char
        elif char == '"':
            quoted = True
        elif char == delimiter:
            row.append(field)
            field = ""
        elif char == "\n":
            row.append(field)
            rows.append(row)
            row, field = [], ""
        elif char != "\r":
            field += char
        index += 1
    if field or row:
        row.append(field)
        rows.append(row)
    return [r for r in rows if r != [""]]


def _cell(text, missing):
    if text.strip().lower() in missing:
        return None
    lowered = text.strip().lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    try:
        if lowered.lstrip("-").isdigit():
            return int(text)
        return float(text)
    except ValueError:
        return text


def load(args):
    """read a csv or json dataset through the run's effects handle. an effect, so an ``oc.``.

    ``format``: "csv" (a header row, then rows) or "json" (either the dataset shape
    itself, or a list of mappings). ``missing`` lists the spellings that mean a
    hole (default ``["", "na", "nan", "null"]``).
    """
    effects = args.get("effects")
    if effects is None:
        raise ValueError("oc.brain.data.load needs the run's effects handle in args['effects']")
    path = args.get("path")
    if not path:
        raise ValueError("oc.brain.data.load needs a 'path' relative to the run's effects root")
    shape = args.get("format", "csv")
    if shape not in ("csv", "json"):
        raise ValueError("load format must be csv or json, got %r" % (shape,))
    for_ = args.get("for") or ("the dataset read from %s" % path)
    text = effects.read_text(path)
    if shape == "json":
        held = json.loads(text)
        if isinstance(held, dict) and "columns" in held and "rows" in held:
            return make(held.get("for", for_), held["columns"], held["rows"])
        if isinstance(held, list):
            columns = []
            for row in held:
                if not isinstance(row, dict):
                    raise ValueError("a json dataset is the dataset shape or a list of mappings")
                for name in row:
                    if name not in columns:
                        columns.append(name)
            return make(for_, columns, [[row.get(name) for name in columns] for row in held])
        raise ValueError("a json dataset is the dataset shape or a list of mappings")
    missing = [str(v).lower() for v in (args.get("missing") or ["", "na", "nan", "null"])]
    delimiter = args.get("delimiter", ",")
    rows = _sniff(text, delimiter)
    if not rows:
        raise ValueError("%s holds no rows at all" % path)
    header = [name.strip() for name in rows[0]]
    body = []
    for line, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise ValueError("line %d of %s has %d cells, the header has %d"
                             % (line, path, len(row), len(header)))
        body.append([_cell(cell, missing) for cell in row])
    return make(for_, header, body)


def builtin(args):
    """one of the built-in dataset Parts by name -- pure, no effect, the same bytes every time."""
    name = args.get("name")
    if name not in BUILT_IN:
        raise ValueError("no built-in dataset %r: one of %s" % (name, ", ".join(sorted(BUILT_IN))))
    return check(json_copy(BUILT_IN[name]))


def json_copy(value):
    return json.loads(json.dumps(value))


LOAD = Calculation("oc.brain.data.load", load)
BUILTIN = Calculation("fn.brain.data.builtin", builtin)

CALCS = {c.address: c for c in (LOAD, BUILTIN)}
