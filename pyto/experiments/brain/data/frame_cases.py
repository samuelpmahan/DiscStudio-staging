"""oracle and benchmark cases for the dataframe-like calculations.

two kinds of authority appear here, and each case says which it is:

* the numeric aggregates have numpy as the reference, named as ``numpy.mean``
  and friends -- the same authority the rest of the brain answers to;
* the relational shape (select, filter, join, pivot, sort, window, missing) has
  no numpy or scipy authority at all. those cases name a SECOND, independent
  implementation written below -- nested loops where the calculation uses a hash
  index, a sort where it uses first-seen order -- and say so in the reference
  name. that gap is a finding, not a shortcut.
"""

import itertools
import math

import numpy as np

import data.frame as frame
from data.datasets import CUSTOMERS, GAPPY, ORDERS, READINGS
from data.table import make, sort_key

WIDE = make("a wider table to group and pivot at size",
            ["key", "bucket", "value"],
            [[i % 37, "b%d" % (i % 5), float((i * 7919) % 1000) / 10.0] for i in range(4000)])
WIDE_SMALL = make(WIDE["for"], WIDE["columns"], WIDE["rows"][:400])
RIGHT = make("the right side of a join at size", ["key", "note"],
             [[i, "n%d" % i] for i in range(37)])


def brute_group_by(table, by, aggregates):
    """an independent group-by: sort, itertools.groupby, numpy for the numbers."""
    at = [table["columns"].index(name) for name in by]
    rows = sorted(table["rows"], key=lambda row: tuple(sort_key(row[i]) for i in at))
    out = []
    for key, members in itertools.groupby(rows, key=lambda row: tuple(sort_key(row[i]) for i in at)):
        members = list(members)
        line = [members[0][i] for i in at]
        for spec in aggregates:
            kind = spec["fn"]
            if spec.get("column") is None:
                line.append(len(members))
                continue
            column_at = table["columns"].index(spec["column"])
            cells = [row[column_at] for row in members]
            present = [c for c in cells if c is not None]
            if kind == "count":
                line.append(len(present))
                continue
            if kind == "count_missing":
                line.append(len(cells) - len(present))
                continue
            if kind == "nunique":
                line.append(len({sort_key(c) for c in present}))
                continue
            if kind == "first":
                line.append(present[0] if present else None)
                continue
            if kind == "last":
                line.append(present[-1] if present else None)
                continue
            numbers = np.asarray([float(c) for c in present], dtype=float)
            if numbers.size == 0:
                line.append(None)
            elif kind == "sum":
                line.append(float(numbers.sum()))
            elif kind == "mean":
                line.append(float(numbers.mean()))
            elif kind == "median":
                line.append(float(np.median(numbers)))
            elif kind == "min":
                line.append(float(numbers.min()))
            elif kind == "max":
                line.append(float(numbers.max()))
            elif numbers.size < 2:
                line.append(None)
            elif kind == "var":
                line.append(float(numbers.var(ddof=1)))
            else:
                line.append(float(numbers.std(ddof=1)))
        out.append(line)
    header = list(by) + [spec.get("as") or ("%s_%s" % (spec.get("column"), spec["fn"])
                                            if spec.get("column") else spec["fn"])
                         for spec in aggregates]
    return {"columns": header, "rows": sorted(out, key=lambda row: tuple(sort_key(c) for c in row))}


def brute_join(left, right, on, how):
    """an independent join: every pair, compared cell by cell. no index at all."""
    left_at = left["columns"].index(on)
    right_at = right["columns"].index(on)
    left_rest = [i for i in range(len(left["columns"])) if i != left_at]
    right_rest = [i for i in range(len(right["columns"])) if i != right_at]
    header = ([on] + [left["columns"][i] for i in left_rest]
              + [right["columns"][i] for i in right_rest])
    rows = []
    for lrow in left["rows"]:
        partners = [r for r in right["rows"] if sort_key(r[right_at]) == sort_key(lrow[left_at])]
        if partners:
            for partner in partners:
                rows.append([lrow[left_at]] + [lrow[i] for i in left_rest]
                            + [partner[i] for i in right_rest])
        elif how in ("left", "outer"):
            rows.append([lrow[left_at]] + [lrow[i] for i in left_rest] + [None] * len(right_rest))
    if how in ("right", "outer"):
        for rrow in right["rows"]:
            if not any(sort_key(l[left_at]) == sort_key(rrow[right_at]) for l in left["rows"]):
                rows.append([rrow[right_at]] + [None] * len(left_rest)
                            + [rrow[i] for i in right_rest])
    return {"columns": header, "rows": rows}


def brute_pivot(table, index, spread, values, kind):
    """an independent pivot: one pass per cell of the output."""
    index_at = table["columns"].index(index)
    spread_at = table["columns"].index(spread)
    values_at = table["columns"].index(values)
    keys = []
    for row in table["rows"]:
        if row[index_at] not in keys:
            keys.append(row[index_at])
    heads = sorted({row[spread_at] for row in table["rows"]}, key=sort_key)
    header = [index] + [str(h) for h in heads]
    rows = []
    for key in keys:
        line = [key]
        for head in heads:
            cells = [row[values_at] for row in table["rows"]
                     if row[index_at] == key and row[spread_at] == head]
            if not cells:
                line.append(None)
            elif kind == "sum":
                line.append(float(np.sum([float(c) for c in cells])))
            elif kind == "mean":
                line.append(float(np.mean([float(c) for c in cells])))
            else:
                line.append(float(np.max([float(c) for c in cells])))
        rows.append(line)
    return {"columns": header, "rows": rows}


def brute_sort(table, name, descending):
    """an independent sort: selection by repeated minimum, not python's sort."""
    at = table["columns"].index(name)
    remaining = [list(row) for row in table["rows"]]
    out = []
    while remaining:
        best = 0
        for i in range(1, len(remaining)):
            if (sort_key(remaining[i][at]) > sort_key(remaining[best][at])) == descending \
                    and sort_key(remaining[i][at]) != sort_key(remaining[best][at]):
                best = i
        out.append(remaining.pop(best))
    return {"columns": list(table["columns"]), "rows": out}


def brute_missing_mean(table, name):
    """an independent mean fill: numpy computes the replacement."""
    at = table["columns"].index(name)
    present = np.asarray([float(row[at]) for row in table["rows"] if row[at] is not None])
    replacement = float(present.mean()) if present.size else None
    rows = [[replacement if (i == at and cell is None) else cell for i, cell in enumerate(row)]
            for row in table["rows"]]
    return {"columns": list(table["columns"]), "rows": rows}


def shape_only(table):
    return {"columns": list(table["columns"]), "rows": [list(r) for r in table["rows"]]}


def sorted_shape(table):
    body = shape_only(table)
    body["rows"] = sorted(body["rows"], key=lambda row: tuple(sort_key(c) for c in row))
    return body


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9, project=None):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance, "project": project}


AGGREGATES = [
    {"column": "price", "fn": "mean"},
    {"column": "price", "fn": "sum"},
    {"column": "price", "fn": "median"},
    {"column": "price", "fn": "min"},
    {"column": "price", "fn": "max"},
    {"column": "price", "fn": "std"},
    {"column": "price", "fn": "var"},
    {"column": "price", "fn": "count"},
    {"column": "price", "fn": "count_missing"},
    {"column": "items", "fn": "sum"},
    {"column": "customer", "fn": "nunique"},
    {"fn": "count", "as": "rows"},
]

ORACLE_CASES = []
for _backend in ("py", "np"):
    ORACLE_CASES.append(_case(
        "fn.brain.data.group_by", "orders.by.region.%s" % _backend, _backend,
        {"table": ORDERS, "by": ["region"], "aggregates": AGGREGATES},
        "numpy.mean/sum/median/min/max/std/var via data.frame_cases.brute_group_by",
        lambda: brute_group_by(ORDERS, ["region"], AGGREGATES), 1e-9, sorted_shape))
    ORACLE_CASES.append(_case(
        "fn.brain.data.group_by", "orders.by.region.customer.%s" % _backend, _backend,
        {"table": ORDERS, "by": ["region", "customer"], "aggregates": AGGREGATES},
        "numpy.mean/sum/median/min/max/std/var via data.frame_cases.brute_group_by",
        lambda: brute_group_by(ORDERS, ["region", "customer"], AGGREGATES), 1e-9, sorted_shape))
    ORACLE_CASES.append(_case(
        "fn.brain.data.pivot", "readings.station.by.month.%s" % _backend, _backend,
        {"table": READINGS, "index": "station", "columns": "month", "values": "celsius",
         "agg": "mean"},
        "numpy.mean via data.frame_cases.brute_pivot",
        lambda: brute_pivot(READINGS, "station", "month", "celsius", "mean"), 1e-9, shape_only))
    ORACLE_CASES.append(_case(
        "fn.brain.data.missing", "gappy.mean.%s" % _backend, _backend,
        {"table": GAPPY, "strategy": "mean", "columns": ["reading"]},
        "numpy.mean via data.frame_cases.brute_missing_mean",
        lambda: brute_missing_mean(GAPPY, "reading"), 1e-9, shape_only))

for _how in ("inner", "left", "right", "outer"):
    ORACLE_CASES.append(_case(
        "fn.brain.data.join", "orders.customers.%s" % _how, "py",
        {"table": ORDERS, "other": CUSTOMERS, "on": "customer", "how": _how},
        "data.frame_cases.brute_join (an independent nested-loop join, no index)",
        (lambda how=_how: brute_join(ORDERS, CUSTOMERS, "customer", how)), 1e-9, sorted_shape))

for _descending in (False, True):
    ORACLE_CASES.append(_case(
        "fn.brain.data.sort", "orders.by.price.%s" % ("desc" if _descending else "asc"), "py",
        {"table": ORDERS, "by": [{"column": "price", "descending": _descending}]},
        "data.frame_cases.brute_sort (an independent selection sort)",
        (lambda descending=_descending: brute_sort(ORDERS, "price", descending)), 1e-9, shape_only))

ORACLE_CASES.append(_case(
    "fn.brain.data.select", "orders.three", "py",
    {"table": ORDERS, "columns": ["order", "region", "price"], "rename": {"order": "id"}},
    "data.frame_cases (the projection written out by hand)",
    lambda: {"columns": ["id", "region", "price"],
             "rows": [[row[0], row[2], row[4]] for row in ORDERS["rows"]]}, 1e-9, shape_only))
ORACLE_CASES.append(_case(
    "fn.brain.data.filter", "orders.east.expedited", "py",
    {"table": ORDERS, "where": [["region", "eq", "east"], ["items", "gte", 3]]},
    "data.frame_cases (the predicate written out by hand)",
    lambda: {"columns": list(ORDERS["columns"]),
             "rows": [list(row) for row in ORDERS["rows"]
                      if row[2] == "east" and row[3] >= 3]}, 1e-9, shape_only))
ORACLE_CASES.append(_case(
    "fn.brain.data.filter", "orders.missing.price", "py",
    {"table": ORDERS, "where": [["price", "is_null"]]},
    "data.frame_cases (the predicate written out by hand)",
    lambda: {"columns": list(ORDERS["columns"]),
             "rows": [list(row) for row in ORDERS["rows"] if row[4] is None]}, 1e-9, shape_only))
ORACLE_CASES.append(_case(
    "fn.brain.data.window", "orders.cumsum.by.customer", "py",
    {"table": ORDERS, "fn": "cumsum", "column": "items", "partition_by": ["customer"],
     "as": "running"},
    "data.frame_cases (the running total written out by hand)",
    lambda: {"columns": list(ORDERS["columns"]) + ["running"],
             "rows": _running(ORDERS, "customer", "items")}, 1e-9, shape_only))
ORACLE_CASES.append(_case(
    "fn.brain.data.shape", "orders", "py", {"table": ORDERS},
    "data.frame_cases (the column kinds read off by hand)",
    lambda: {"rows": 12, "columns": list(ORDERS["columns"]),
             "kinds": {"order": "number", "customer": "text", "region": "text",
                       "items": "number", "price": "number", "expedited": "boolean"}}))
ORACLE_CASES.append(_case(
    "fn.brain.data.missing_report", "gappy", "py", {"table": GAPPY},
    "data.frame_cases (the holes counted by hand)",
    lambda: {"rows": 7,
             "columns": {"step": {"missing": 0, "present": 7, "fraction": 0.0},
                         "reading": {"missing": 4, "present": 3, "fraction": 4 / 7},
                         "label": {"missing": 2, "present": 5, "fraction": 2 / 7}},
             "complete_rows": 3}))


def _running(table, key, value):
    key_at = table["columns"].index(key)
    value_at = table["columns"].index(value)
    totals = {}
    out = []
    for row in table["rows"]:
        totals[row[key_at]] = totals.get(row[key_at], 0.0) + float(row[value_at])
        out.append(list(row) + [totals[row[key_at]]])
    return out


BENCH_CASES = []
for _backend in ("py", "np"):
    for _size, _table in (("rows=400", WIDE_SMALL), ("rows=4000", WIDE)):
        BENCH_CASES.append({
            "calc": "fn.brain.data.group_by", "backend": _backend, "size": _size,
            "make_args": (lambda table=_table, backend=_backend: {
                "table": table, "by": ["key"], "backend": backend,
                "aggregates": [{"column": "value", "fn": "mean"},
                               {"column": "value", "fn": "sum"},
                               {"column": "value", "fn": "std"},
                               {"column": "value", "fn": "median"},
                               {"fn": "count", "as": "rows"}]})})
        BENCH_CASES.append({
            "calc": "fn.brain.data.pivot", "backend": _backend, "size": _size,
            "make_args": (lambda table=_table, backend=_backend: {
                "table": table, "index": "key", "columns": "bucket", "values": "value",
                "agg": "mean", "backend": backend})})

CALCS = frame.CALCS
