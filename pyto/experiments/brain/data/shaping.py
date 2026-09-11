"""two more shapes: wide back to long, and a whole table described.

``fn.brain.data.melt`` is ``fn.brain.data.pivot``'s inverse.
``fn.brain.data.describe_table`` is the one place the data vertical calls the
stats vertical: a per-column summary built out of `fn.brain.stats.*`, so there
is exactly one definition of a quantile in the brain and the table summary uses
it rather than writing a second one.
"""

from pyto import Calculation

import stats.descriptive as descriptive
from data.table import check, column, index_of, make


def melt(args):
    """the wide table folded long: one row per (id columns, variable, value).

    ``id_vars`` stay as they are; ``value_vars`` (default: everything else)
    become a ``var_name``/``value_name`` pair. ``drop_missing`` leaves out the
    cells that are holes.
    """
    table = check(args["table"])
    columns = list(table["columns"])
    id_vars = args.get("id_vars") or []
    if isinstance(id_vars, str):
        id_vars = [id_vars]
    for name in id_vars:
        index_of(table, name)
    value_vars = args.get("value_vars")
    if value_vars is None:
        value_vars = [name for name in columns if name not in id_vars]
    if isinstance(value_vars, str):
        value_vars = [value_vars]
    if not value_vars:
        raise ValueError("melt needs at least one column to fold")
    for name in value_vars:
        index_of(table, name)
    overlap = set(id_vars) & set(value_vars)
    if overlap:
        raise ValueError("a column cannot be both an id and a value: %r" % sorted(overlap))
    var_name = args.get("var_name", "variable")
    value_name = args.get("value_name", "value")
    header = list(id_vars) + [var_name, value_name]
    if len(set(header)) != len(header):
        raise ValueError("melt would produce a repeated column name: %r" % (header,))
    id_at = [index_of(table, name) for name in id_vars]
    drop_missing = bool(args.get("drop_missing", False))
    rows = []
    for row in table["rows"]:
        for name in value_vars:
            cell = row[index_of(table, name)]
            if drop_missing and cell is None:
                continue
            rows.append([row[i] for i in id_at] + [name, cell])
    return make(args.get("for") or "%s folded long" % table.get("for", "a dataset"),
                header, rows)


SUMMARY = ("n", "missing", "mean", "stdev", "min", "q25", "median", "q75", "max")


def describe_table(args):
    """a per-column summary of a dataset Part, built out of the stats vertical.

    numeric columns get the nine-number summary; every other column gets its
    count, its holes and how many distinct values it holds. Parts in, Parts out:
    the answer is itself a dataset Part, one row per column.
    """
    table = check(args["table"])
    names = args.get("columns") or list(table["columns"])
    backend = args.get("backend", "py")
    if backend not in ("py", "np"):
        raise ValueError("unknown backend %r for describe_table: py or np" % (backend,))
    header = ["column", "kind", "n", "missing", "distinct"] + list(SUMMARY[2:])
    rows = []
    for name in names:
        cells = column(table, name)
        present = [c for c in cells if c is not None]
        numbers = [float(c) for c in present
                   if isinstance(c, (int, float)) and not isinstance(c, bool)]
        kind = "number" if present and len(numbers) == len(present) else (
            "empty" if not present else "other")
        line = [name, kind, len(present), len(cells) - len(present),
                len({repr(c) for c in present})]
        if kind == "number" and numbers:
            stats_args = {"values": numbers, "backend": backend}
            line += [
                descriptive.mean(stats_args),
                descriptive.stdev(dict(stats_args, ddof=1)) if len(numbers) > 1 else None,
                min(numbers),
                descriptive.quantile(dict(stats_args, q=0.25)),
                descriptive.median(stats_args),
                descriptive.quantile(dict(stats_args, q=0.75)),
                max(numbers),
            ]
        else:
            line += [None] * 7
        rows.append(line)
    return make(args.get("for") or "a per-column summary of %s" % table.get("for", "a dataset"),
                header, rows)


MELT = Calculation("fn.brain.data.melt", melt)
DESCRIBE_TABLE = Calculation("fn.brain.data.describe_table", describe_table)

CALCS = {c.address: c for c in (MELT, DESCRIBE_TABLE)}
