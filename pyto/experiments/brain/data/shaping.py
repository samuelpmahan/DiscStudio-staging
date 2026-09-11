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


DIRECTIONS = ("backward", "forward", "nearest")


def rolling_join(args):
    """an as-of join: every left row takes the right row nearest its key.

    the one join a time series actually wants. ``on`` is an ordered numeric key
    in both tables; ``direction`` is "backward" (the last right row at or before
    the left key, the default), "forward" (the first at or after) or "nearest".
    ``tolerance`` refuses a match further away than that. ``by`` restricts the
    search to right rows whose ``by`` columns match, so several series can share
    one table.
    """
    left = check(args["table"], "table")
    right = check(args["other"], "other")
    on = args.get("on")
    if not on:
        raise ValueError("an as-of join needs 'on': the ordered key both tables carry")
    direction = args.get("direction", "backward")
    if direction not in DIRECTIONS:
        raise ValueError("direction must be one of %s, got %r" % (", ".join(DIRECTIONS), direction))
    tolerance = args.get("tolerance")
    tolerance = None if tolerance is None else float(tolerance)
    if tolerance is not None and tolerance < 0.0:
        raise ValueError("a tolerance cannot be negative")
    by = args.get("by") or []
    if isinstance(by, str):
        by = [by]
    left_key = index_of(left, on, "left key")
    right_key = index_of(right, on, "right key")
    left_by = [index_of(left, name, "left by") for name in by]
    right_by = [index_of(right, name, "right by") for name in by]
    suffixes = args.get("suffixes") or ["_left", "_right"]
    right_rest = [i for i in range(len(right["columns"]))
                  if i != right_key and i not in right_by]
    clashes = set(left["columns"]) & {right["columns"][i] for i in right_rest}
    header = list(left["columns"]) + [
        right["columns"][i] + (suffixes[1] if right["columns"][i] in clashes else "")
        for i in right_rest]
    if len(set(header)) != len(header):
        raise ValueError("this as-of join would produce a repeated column name: %r" % (header,))
    groups = {}
    for row in right["rows"]:
        if row[right_key] is None:
            continue
        groups.setdefault(tuple(str(row[i]) for i in right_by), []).append(row)
    for members in groups.values():
        members.sort(key=lambda row: float(row[right_key]))
    rows = []
    for row in left["rows"]:
        partner = None
        if row[left_key] is not None:
            members = groups.get(tuple(str(row[i]) for i in left_by), [])
            partner = _nearest(members, right_key, float(row[left_key]), direction, tolerance)
        rows.append(list(row) + ([partner[i] for i in right_rest] if partner is not None
                                 else [None] * len(right_rest)))
    return make(args.get("for") or "%s with the nearest %s taken as of %s"
                % (left.get("for", "a dataset"), right.get("for", "another dataset"), on),
                header, rows)


def _nearest(members, key_at, key, direction, tolerance):
    """the member nearest ``key`` in the direction asked for, within the tolerance."""
    low, high = 0, len(members)
    while low < high:
        middle = (low + high) // 2
        if float(members[middle][key_at]) <= key:
            low = middle + 1
        else:
            high = middle
    before = members[low - 1] if low > 0 else None
    after = members[low] if low < len(members) else None
    if direction == "backward":
        chosen = before
    elif direction == "forward":
        chosen = after
    else:
        if before is None:
            chosen = after
        elif after is None:
            chosen = before
        else:
            chosen = (before if key - float(before[key_at]) <= float(after[key_at]) - key
                      else after)
    if chosen is None:
        return None
    if tolerance is not None and abs(float(chosen[key_at]) - key) > tolerance:
        return None
    return chosen


MELT = Calculation("fn.brain.data.melt", melt)
ROLLING_JOIN = Calculation("fn.brain.data.rolling_join", rolling_join)
DESCRIBE_TABLE = Calculation("fn.brain.data.describe_table", describe_table)

CALCS = {c.address: c for c in (MELT, ROLLING_JOIN, DESCRIBE_TABLE)}
