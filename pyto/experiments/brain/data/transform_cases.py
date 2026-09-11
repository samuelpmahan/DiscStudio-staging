"""oracle and benchmark cases for the column transforms.

the numeric transforms answer to scipy and numpy (``scipy.stats.zscore``,
``scipy.stats.rankdata``, ``scipy.stats.iqr``, ``numpy.quantile``). the
relational ones -- crosstab, dedupe, concat, sample -- have no library
authority, so their cases name a second implementation written below and say so,
exactly as the rest of the data vertical does.
"""

import numpy as np
from scipy import stats as sp_stats

import data.transform as transform
from data.datasets import CUSTOMERS, GAPPY, ORDERS
from data.table import column, sort_key


class Ledger:
    """a stand-in for the effects handle: fixed uniforms, so the draw is a fact."""

    def __init__(self, draws):
        self.draws = list(draws)
        self.asked = []

    def random(self, n):
        self.asked.append(n)
        out, self.draws = self.draws[:n], self.draws[n:]
        if len(out) != n:
            raise AssertionError("the ledger ran out of draws")
        return out


DRAWS = [((i * 7919 + 104729) % 1009) / 1009.0 for i in range(64)]


def added(name):
    """the transforms add one column; the oracle looks at exactly that column."""
    return lambda got: column(got, name)


def brute_zscore(table, name, ddof=0):
    """scipy.stats.zscore over the present cells, holes left as holes."""
    cells = column(table, name)
    present = np.asarray([float(c) for c in cells if c is not None])
    scores = sp_stats.zscore(present, ddof=ddof)
    out = []
    place = 0
    for cell in cells:
        if cell is None:
            out.append(None)
        else:
            out.append(float(scores[place]))
            place += 1
    return out


def brute_unit(table, name):
    cells = column(table, name)
    present = np.asarray([float(c) for c in cells if c is not None])
    low, high = float(present.min()), float(present.max())
    return [None if c is None else (float(c) - low) / (high - low) for c in cells]


def brute_rank(table, name):
    cells = column(table, name)
    present = [float(c) for c in cells if c is not None]
    ranks = sp_stats.rankdata(present)
    out = []
    place = 0
    for cell in cells:
        if cell is None:
            out.append(None)
        else:
            out.append(float(ranks[place]))
            place += 1
    return out


def brute_iqr_flags(table, name, k=1.5):
    cells = column(table, name)
    present = np.asarray([float(c) for c in cells if c is not None])
    spread = float(sp_stats.iqr(present))
    low = float(np.quantile(present, 0.25)) - k * spread
    high = float(np.quantile(present, 0.75)) + k * spread
    return [None if c is None else not (low <= float(c) <= high) for c in cells]


def brute_crosstab(table, index, columns):
    """an independent crosstab: one full pass per cell of the output."""
    # the ORDER is the vertical's documented convention (data.table.sort_key:
    # missing first, then numbers, then text), not the thing under test; the
    # COUNTS are what this second implementation computes independently.
    down = sorted({row[table["columns"].index(index)] for row in table["rows"]}, key=sort_key)
    across = sorted({row[table["columns"].index(columns)] for row in table["rows"]},
                    key=sort_key)
    rows = []
    for one in down:
        line = [one]
        for other in across:
            line.append(sum(1 for row in table["rows"]
                            if row[table["columns"].index(index)] == one
                            and row[table["columns"].index(columns)] == other))
        rows.append(line)
    return {"columns": [index] + [("" if v is None else str(v)) for v in across], "rows": rows}


def brute_dedupe(table, subset):
    """an independent dedupe: keep a row only when no earlier row matched it."""
    at = [table["columns"].index(name) for name in subset]
    rows = []
    for index, row in enumerate(table["rows"]):
        key = [row[i] for i in at]
        if not any([earlier[i] for i in at] == key for earlier in table["rows"][:index]):
            rows.append(list(row))
    return {"columns": list(table["columns"]), "rows": rows}


def shape_only(table):
    return {"columns": list(table["columns"]), "rows": [list(r) for r in table["rows"]]}


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9, project=None):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance, "project": project}


ORACLE_CASES = []
for _backend in ("py", "np"):
    ORACLE_CASES.append(_case(
        "fn.brain.data.standardize", "orders.items.%s" % _backend, _backend,
        {"table": ORDERS, "column": "items"}, "scipy.stats.zscore",
        lambda: brute_zscore(ORDERS, "items"), 1e-9, added("items_z")))
    ORACLE_CASES.append(_case(
        "fn.brain.data.standardize", "orders.price.holes.ddof1.%s" % _backend, _backend,
        {"table": ORDERS, "column": "price", "ddof": 1}, "scipy.stats.zscore",
        lambda: brute_zscore(ORDERS, "price", ddof=1), 1e-9, added("price_z")))
    ORACLE_CASES.append(_case(
        "fn.brain.data.normalize", "orders.price.%s" % _backend, _backend,
        {"table": ORDERS, "column": "price"}, "numpy.min and numpy.max",
        lambda: brute_unit(ORDERS, "price"), 1e-9, added("price_unit")))
    ORACLE_CASES.append(_case(
        "fn.brain.data.rank_column", "orders.items.%s" % _backend, _backend,
        {"table": ORDERS, "column": "items"}, "scipy.stats.rankdata",
        lambda: brute_rank(ORDERS, "items"), 1e-9, added("items_rank")))
    ORACLE_CASES.append(_case(
        "fn.brain.data.outliers", "orders.price.iqr.%s" % _backend, _backend,
        {"table": ORDERS, "column": "price"}, "scipy.stats.iqr and numpy.quantile",
        lambda: brute_iqr_flags(ORDERS, "price"), 1e-9, added("price_outlier")))
    ORACLE_CASES.append(_case(
        "fn.brain.data.bin_column", "orders.items.quantile.%s" % _backend, _backend,
        {"table": ORDERS, "column": "items", "bins": 4, "rule": "quantile"},
        "numpy.quantile for the edges",
        lambda: [float(v) for v in np.quantile(
            [float(c) for c in column(ORDERS, "items")], [0.0, 0.25, 0.5, 0.75, 1.0])],
        1e-9, (lambda got: got["edges"])))

ORACLE_CASES.append(_case(
    "fn.brain.data.crosstab", "orders.region.by.expedited", "py",
    {"table": ORDERS, "index": "region", "columns": "expedited"},
    "data.transform_cases.brute_crosstab (an independent full pass per cell)",
    lambda: brute_crosstab(ORDERS, "region", "expedited"), 1e-9, shape_only))
ORACLE_CASES.append(_case(
    "fn.brain.data.dedupe", "orders.by.customer", "py",
    {"table": ORDERS, "subset": ["customer"]},
    "data.transform_cases.brute_dedupe (an independent quadratic scan)",
    lambda: brute_dedupe(ORDERS, ["customer"]), 1e-9, shape_only))
ORACLE_CASES.append(_case(
    "fn.brain.data.dedupe", "gappy.whole.rows", "py", {"table": GAPPY},
    "data.transform_cases.brute_dedupe (an independent quadratic scan)",
    lambda: brute_dedupe(GAPPY, list(GAPPY["columns"])), 1e-9, shape_only))
ORACLE_CASES.append(_case(
    "fn.brain.data.concat", "orders.customers", "py",
    {"tables": [ORDERS, CUSTOMERS]},
    "data.transform_cases (the union written out by hand)",
    lambda: {"columns": list(ORDERS["columns"]) + ["tier", "since"],
             "rows": [list(row) + [None, None] for row in ORDERS["rows"]]
                     + [[None, row[0], None, None, None, None, row[1], row[2]]
                        for row in CUSTOMERS["rows"]]},
    1e-9, shape_only))
ORACLE_CASES.append(_case(
    "oc.brain.data.sample", "orders.five.no.replacement", "py",
    {"table": ORDERS, "n": 5},
    "data.transform_cases (the partial fisher-yates written out by hand)",
    lambda: _brute_sample(ORDERS, 5, DRAWS), 1e-9, shape_only))


def _brute_sample(table, n, draws):
    total = len(table["rows"])
    pool = list(range(total))
    picked = []
    for index in range(n):
        left = total - index
        place = index + min(left - 1, int(draws[index] * left))
        pool[index], pool[place] = pool[place], pool[index]
        picked.append(pool[index])
    return {"columns": list(table["columns"]),
            "rows": [list(table["rows"][i]) for i in picked]}


_BIG = {"for": "a wider table for the transform benchmarks",
        "columns": ["key", "value"],
        "rows": [[i % 53, float((i * 7919) % 1000) / 10.0] for i in range(4000)]}
_MID = {"for": _BIG["for"], "columns": _BIG["columns"], "rows": _BIG["rows"][:400]}

BENCH_CASES = []
for _backend in ("py", "np"):
    for _size, _table in (("rows=400", _MID), ("rows=4000", _BIG)):
        for _calc, _extra in (("fn.brain.data.standardize", {}),
                              ("fn.brain.data.rank_column", {}),
                              ("fn.brain.data.outliers", {})):
            BENCH_CASES.append({
                "calc": _calc, "backend": _backend, "size": _size,
                "make_args": (lambda table=_table, backend=_backend, extra=_extra:
                              dict(extra, table=table, column="value", backend=backend))})

CALCS = transform.CALCS
