"""the column transforms a real pipeline needs, as Calculations over dataset Parts.

Parts in, Parts out: every one of these takes a table Part and hands back a table
Part, so a pipeline is a PCR and not a script. the numeric ones call the stats
vertical rather than writing a second definition of a mean or a quantile.

drawing rows is an effect, so ``oc.brain.data.sample`` takes the run's effects
handle and the draw lands on the ledger.
"""

import math

from pyto import Calculation

import stats.descriptive as descriptive
from data.table import check, column, index_of, make, numeric, sort_key

OUTLIER_RULES = ("iqr", "zscore")
BIN_RULES = ("width", "quantile")


def _backend(args, allowed=("py", "np")):
    backend = args.get("backend", "py")
    if backend not in allowed:
        raise ValueError("unknown backend %r for a transform: %s"
                         % (backend, " or ".join(allowed)))
    return backend


def _numeric_column(table, name):
    cells = column(table, name)
    values = numeric([c for c in cells if c is not None], "column %r" % name)
    if not values:
        raise ValueError("column %r has no numbers in it" % name)
    return cells, values


def _added(table, name, label, values, for_):
    if label in table["columns"]:
        raise ValueError("the column %r is already in this dataset" % label)
    rows = [list(row) + [value] for row, value in zip(table["rows"], values)]
    return make(for_, list(table["columns"]) + [label], rows)


def standardize(args):
    """a column in standard-deviation units, added beside it. reference: scipy.stats.zscore."""
    table = check(args["table"])
    name = args["column"]
    backend = _backend(args)
    cells, values = _numeric_column(table, name)
    ddof = int(args.get("ddof", 0))
    centre = descriptive.mean({"values": values, "backend": backend})
    spread = descriptive.stdev({"values": values, "ddof": ddof, "backend": backend})
    if spread == 0.0:
        raise ValueError("column %r has no spread, so it cannot be standardised" % name)
    out = [None if cell is None else (float(cell) - centre) / spread for cell in cells]
    return _added(table, name, args.get("as") or "%s_z" % name, out,
                  args.get("for") or "%s with %s in standard-deviation units"
                  % (table.get("for", "a dataset"), name))


def normalize(args):
    """a column rescaled to [0, 1], added beside it. reference: numpy.min and numpy.max."""
    table = check(args["table"])
    name = args["column"]
    _backend(args)
    cells, values = _numeric_column(table, name)
    low, high = min(values), max(values)
    if high == low:
        raise ValueError("column %r is constant, so it cannot be rescaled" % name)
    out = [None if cell is None else (float(cell) - low) / (high - low) for cell in cells]
    return _added(table, name, args.get("as") or "%s_unit" % name, out,
                  args.get("for") or "%s with %s rescaled to [0, 1]"
                  % (table.get("for", "a dataset"), name))


def rank_column(args):
    """a column's average ranks, added beside it. reference: scipy.stats.rankdata."""
    from stats.correlation import rank

    table = check(args["table"])
    name = args["column"]
    _backend(args)
    cells = column(table, name)
    present = [(i, cell) for i, cell in enumerate(cells) if cell is not None]
    ranks = rank({"values": [float(cell) for _, cell in present]}) if present else []
    out = [None] * len(cells)
    for (i, _), value in zip(present, ranks):
        out[i] = value
    descending = bool(args.get("descending", False))
    if descending and present:
        top = len(present) + 1.0
        out = [None if v is None else top - v for v in out]
    return _added(table, name, args.get("as") or "%s_rank" % name, out,
                  args.get("for") or "%s with %s ranked" % (table.get("for", "a dataset"), name))


def bin_column(args):
    """a numeric column cut into bins, added beside it as a label.

    ``rule``: "width" (equal-width edges between min and max) or "quantile"
    (equal-count edges). reference: numpy.quantile for the quantile edges.
    """
    table = check(args["table"])
    name = args["column"]
    backend = _backend(args)
    rule = args.get("rule", "width")
    if rule not in BIN_RULES:
        raise ValueError("bin rule must be width or quantile, got %r" % (rule,))
    count = int(args.get("bins", 4))
    if count < 1:
        raise ValueError("a binning needs at least one bin")
    cells, values = _numeric_column(table, name)
    low, high = min(values), max(values)
    if high == low:
        raise ValueError("column %r is constant, so it cannot be binned" % name)
    if rule == "width":
        step = (high - low) / count
        edges = [low + step * i for i in range(count)] + [high]
    else:
        edges = descriptive.quantile(
            {"values": values, "q": [i / count for i in range(count + 1)], "backend": backend})
        edges = sorted(set(edges))
        if len(edges) < 2:
            raise ValueError("column %r cannot be cut into %d quantile bins" % (name, count))
    labels = args.get("labels")
    if labels is not None and len(labels) != len(edges) - 1:
        raise ValueError("there are %d bins and %d labels" % (len(edges) - 1, len(labels)))
    out = []
    for cell in cells:
        if cell is None:
            out.append(None)
            continue
        value = float(cell)
        place = 0
        for index in range(len(edges) - 1):
            if value >= edges[index]:
                place = index
        out.append(labels[place] if labels else
                   "[%g, %g%s" % (edges[place], edges[place + 1],
                                  "]" if place == len(edges) - 2 else ")"))
    table_out = _added(table, name, args.get("as") or "%s_bin" % name, out,
                       args.get("for") or "%s with %s cut into %d bins"
                       % (table.get("for", "a dataset"), name, len(edges) - 1))
    table_out["edges"] = edges
    return table_out


def crosstab(args):
    """the counts of every pair of values of two columns, as a wide table."""
    table = check(args["table"])
    rows_name = args["index"]
    columns_name = args["columns"]
    row_at = index_of(table, rows_name)
    column_at = index_of(table, columns_name)
    down = []
    across = []
    counts = {}
    for row in table["rows"]:
        key = (sort_key(row[row_at]), sort_key(row[column_at]))
        if row[row_at] not in down:
            down.append(row[row_at])
        if row[column_at] not in across:
            across.append(row[column_at])
        counts[key] = counts.get(key, 0) + 1
    down.sort(key=sort_key)
    across.sort(key=sort_key)
    header = [rows_name] + [("" if one is None else str(one)) for one in across]
    if len(set(header)) != len(header):
        raise ValueError("this crosstab would produce a repeated column name: %r" % (header,))
    body = []
    for one in down:
        body.append([one] + [counts.get((sort_key(one), sort_key(other)), 0)
                             for other in across])
    if args.get("margins"):
        header.append("total")
        for line in body:
            line.append(sum(line[1:]))
        body.append(["total"] + [sum(line[i] for line in body)
                                 for i in range(1, len(header))])
    return make(args.get("for") or "%s by %s, counted" % (rows_name, columns_name), header, body)


def dedupe(args):
    """the rows left once repeats are dropped, keeping the first (or the last)."""
    table = check(args["table"])
    subset = args.get("subset") or list(table["columns"])
    at = [index_of(table, name) for name in subset]
    keep = args.get("keep", "first")
    if keep not in ("first", "last"):
        raise ValueError("dedupe keep must be first or last, got %r" % (keep,))
    seen = {}
    order = []
    for index, row in enumerate(table["rows"]):
        key = tuple(sort_key(row[i]) for i in at)
        if key not in seen:
            order.append(key)
        if key not in seen or keep == "last":
            seen[key] = list(row)
    return make(args.get("for") or "%s with repeats dropped" % table.get("for", "a dataset"),
                table["columns"], [seen[key] for key in order])


def concat(args):
    """two (or more) tables stacked, aligned by column name.

    a column missing from one of them is filled with ``None`` unless
    ``strict`` says the headers must match exactly.
    """
    tables = args.get("tables")
    if not tables or len(tables) < 2:
        raise ValueError("concat needs at least two tables")
    checked = [check(one, "table %d" % index) for index, one in enumerate(tables)]
    if args.get("strict"):
        first = list(checked[0]["columns"])
        for index, one in enumerate(checked[1:], start=1):
            if list(one["columns"]) != first:
                raise ValueError("table %d has a different header: %r against %r"
                                 % (index, list(one["columns"]), first))
    header = []
    for one in checked:
        for name in one["columns"]:
            if name not in header:
                header.append(name)
    rows = []
    for one in checked:
        columns = list(one["columns"])
        for row in one["rows"]:
            rows.append([row[columns.index(name)] if name in columns else None
                         for name in header])
    return make(args.get("for") or "%d tables stacked" % len(checked), header, rows)


def outliers(args):
    """a boolean column flagging the outliers of a numeric column.

    ``rule``: "iqr" (outside q25 - k*iqr .. q75 + k*iqr, k default 1.5) or
    "zscore" (|z| above ``threshold``, default 3). reference: scipy.stats.iqr
    and scipy.stats.zscore.
    """
    table = check(args["table"])
    name = args["column"]
    backend = _backend(args)
    rule = args.get("rule", "iqr")
    if rule not in OUTLIER_RULES:
        raise ValueError("outlier rule must be iqr or zscore, got %r" % (rule,))
    cells, values = _numeric_column(table, name)
    if rule == "iqr":
        k = float(args.get("k", 1.5))
        low = descriptive.quantile({"values": values, "q": 0.25, "backend": backend})
        high = descriptive.quantile({"values": values, "q": 0.75, "backend": backend})
        spread = high - low
        floor, ceiling = low - k * spread, high + k * spread
        flags = [None if cell is None else not (floor <= float(cell) <= ceiling)
                 for cell in cells]
        bounds = {"low": floor, "high": ceiling}
    else:
        threshold = float(args.get("threshold", 3.0))
        centre = descriptive.mean({"values": values, "backend": backend})
        spread = descriptive.stdev({"values": values, "backend": backend})
        if spread == 0.0:
            raise ValueError("column %r has no spread, so no z-score can be taken" % name)
        flags = [None if cell is None else abs((float(cell) - centre) / spread) > threshold
                 for cell in cells]
        bounds = {"low": centre - threshold * spread, "high": centre + threshold * spread}
    out = _added(table, name, args.get("as") or "%s_outlier" % name, flags,
                 args.get("for") or "%s with the outliers of %s flagged by the %s rule"
                 % (table.get("for", "a dataset"), name, rule))
    out["bounds"] = bounds
    out["rule"] = rule
    out["outliers"] = sum(1 for flag in flags if flag)
    return out


def sample(args):
    """``n`` rows drawn through the run's effects handle. an effect, so an ``oc.``.

    ``replace`` draws with replacement (default false). the draws land on the
    ledger, so the same record replays to the same sample.
    """
    effects = args.get("effects")
    if effects is None:
        raise ValueError("oc.brain.data.sample needs the run's effects handle in args['effects']")
    table = check(args["table"])
    n = args.get("n", 1)
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("sample needs a non-negative integer n, got %r" % (n,))
    replace = bool(args.get("replace", False))
    total = len(table["rows"])
    if total == 0:
        raise ValueError("there are no rows to draw from")
    if not replace and n > total:
        raise ValueError("cannot draw %d of %d rows without replacement" % (n, total))
    if replace:
        draws = effects.random(n)
        picked = [min(total - 1, int(u * total)) for u in draws]
    else:
        # a partial fisher-yates over the row positions, one draw per pick: the
        # ledger therefore holds exactly n numbers and the shuffle is replayable.
        draws = effects.random(n)
        pool = list(range(total))
        picked = []
        for index, u in enumerate(draws):
            left = total - index
            place = index + min(left - 1, int(u * left))
            pool[index], pool[place] = pool[place], pool[index]
            picked.append(pool[index])
    rows = [list(table["rows"][i]) for i in picked]
    return make(args.get("for") or "%d rows drawn from %s"
                % (n, table.get("for", "a dataset")), table["columns"], rows)


STANDARDIZE = Calculation("fn.brain.data.standardize", standardize)
NORMALIZE = Calculation("fn.brain.data.normalize", normalize)
RANK_COLUMN = Calculation("fn.brain.data.rank_column", rank_column)
BIN_COLUMN = Calculation("fn.brain.data.bin_column", bin_column)
CROSSTAB = Calculation("fn.brain.data.crosstab", crosstab)
DEDUPE = Calculation("fn.brain.data.dedupe", dedupe)
CONCAT = Calculation("fn.brain.data.concat", concat)
OUTLIERS = Calculation("fn.brain.data.outliers", outliers)
SAMPLE = Calculation("oc.brain.data.sample", sample)

CALCS = {c.address: c for c in (STANDARDIZE, NORMALIZE, RANK_COLUMN, BIN_COLUMN,
                                CROSSTAB, DEDUPE, CONCAT, OUTLIERS, SAMPLE)}
