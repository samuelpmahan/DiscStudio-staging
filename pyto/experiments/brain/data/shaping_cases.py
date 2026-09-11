"""oracle and benchmark cases for melt and the table summary.

melt has no numpy authority (numpy has no long/wide), so its case names a second
implementation written here. describe_table does: every number in it comes from
numpy, computed independently of the stats vertical the calculation calls.
"""

import numpy as np

import data.shaping as shaping
from data.datasets import GAPPY, ORDERS, READINGS
from data.frame import pivot

WIDE = pivot({"table": READINGS, "index": "station", "columns": "month",
              "values": "celsius", "agg": "mean"})


def brute_melt(table, id_vars, value_vars, var_name, value_name, drop_missing=False):
    """an independent fold: one pass per value column, appended in column order."""
    columns = list(table["columns"])
    rows = []
    for row in table["rows"]:
        for name in value_vars:
            cell = row[columns.index(name)]
            if drop_missing and cell is None:
                continue
            rows.append([row[columns.index(one)] for one in id_vars] + [name, cell])
    return {"columns": list(id_vars) + [var_name, value_name], "rows": rows}


def brute_describe(table, names=None):
    """numpy for every number: the authority the table summary answers to."""
    columns = list(table["columns"])
    names = names or columns
    header = ["column", "kind", "n", "missing", "distinct", "mean", "stdev", "min",
              "q25", "median", "q75", "max"]
    rows = []
    for name in names:
        cells = [row[columns.index(name)] for row in table["rows"]]
        present = [c for c in cells if c is not None]
        numbers = [float(c) for c in present
                   if isinstance(c, (int, float)) and not isinstance(c, bool)]
        kind = "number" if present and len(numbers) == len(present) else (
            "empty" if not present else "other")
        line = [name, kind, len(present), len(cells) - len(present),
                len({repr(c) for c in present})]
        if kind == "number" and numbers:
            a = np.asarray(numbers, dtype=float)
            line += [float(a.mean()),
                     float(a.std(ddof=1)) if a.size > 1 else None,
                     float(a.min()),
                     float(np.quantile(a, 0.25)),
                     float(np.median(a)),
                     float(np.quantile(a, 0.75)),
                     float(a.max())]
        else:
            line += [None] * 7
        rows.append(line)
    return {"columns": header, "rows": rows}


def shape_only(table):
    return {"columns": list(table["columns"]), "rows": [list(r) for r in table["rows"]]}


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9, project=shape_only):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance, "project": project}


ORACLE_CASES = [
    _case("fn.brain.data.melt", "readings.wide.to.long", "py",
          {"table": WIDE, "id_vars": ["station"], "var_name": "month",
           "value_name": "celsius"},
          "data.shaping_cases.brute_melt (an independent fold, column by column)",
          lambda: brute_melt(WIDE, ["station"], ["feb", "jan", "mar"], "month", "celsius")),
    _case("fn.brain.data.melt", "readings.drop.missing", "py",
          {"table": WIDE, "id_vars": ["station"], "var_name": "month",
           "value_name": "celsius", "drop_missing": True},
          "data.shaping_cases.brute_melt (an independent fold, column by column)",
          lambda: brute_melt(WIDE, ["station"], ["feb", "jan", "mar"], "month", "celsius",
                             drop_missing=True)),
    _case("fn.brain.data.melt", "gappy.two.ids", "py",
          {"table": GAPPY, "id_vars": ["step"], "value_vars": ["reading", "label"]},
          "data.shaping_cases.brute_melt (an independent fold, column by column)",
          lambda: brute_melt(GAPPY, ["step"], ["reading", "label"], "variable", "value")),
]
for _backend in ("py", "np"):
    ORACLE_CASES.append(_case(
        "fn.brain.data.describe_table", "orders.%s" % _backend, _backend,
        {"table": ORDERS},
        "numpy.mean/std/median/quantile per column",
        lambda: brute_describe(ORDERS)))
    ORACLE_CASES.append(_case(
        "fn.brain.data.describe_table", "gappy.%s" % _backend, _backend,
        {"table": GAPPY},
        "numpy.mean/std/median/quantile per column",
        lambda: brute_describe(GAPPY)))

BENCH_CASES = []

CALCS = shaping.CALCS
