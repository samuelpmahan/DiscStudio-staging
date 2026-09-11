"""dataframe-like Calculations over the dataset shape: Parts in, Parts out.

every one takes a table Part and returns a table Part (or, for a report, a
json-able mapping). the predicate of a filter, the aggregate of a group-by and
the ordering of a sort are all DATA -- lists and strings, never callables -- so
the whole program is json-able and lands on a record intact.

``args["backend"]``: "py" everywhere (the reference), "np" where numpy pays --
group-by aggregation and the numeric column reductions.
"""

import math

from pyto import Calculation

from data.table import check, column, index_of, make, numeric, sort_key

COMPARISONS = ("eq", "ne", "lt", "lte", "gt", "gte", "in", "not_in",
               "contains", "is_null", "not_null")
AGGREGATES = ("count", "count_missing", "sum", "mean", "median", "min", "max",
              "var", "std", "nunique", "first", "last")
HOWS = ("inner", "left", "right", "outer")


def _backend(args, allowed=("py", "np")):
    backend = args.get("backend", "py")
    if backend not in allowed:
        raise ValueError("unknown backend %r for a data calculation: %s"
                         % (backend, " or ".join(allowed)))
    return backend


def _for(args, default):
    return args.get("for") or default


def select(args):
    """the named columns, in the order named, optionally renamed. Parts in, Parts out."""
    table = check(args["table"])
    columns = args.get("columns")
    if columns is None:
        columns = list(table["columns"])
    rename = args.get("rename") or {}
    at = [index_of(table, name) for name in columns]
    header = [rename.get(name, name) for name in columns]
    if len(set(header)) != len(header):
        raise ValueError("select would produce a repeated column name: %r" % (header,))
    rows = [[row[i] for i in at] for row in table["rows"]]
    return make(_for(args, "the columns %s of %s" % (", ".join(columns), table.get("for", "a dataset"))),
                header, rows)


def _cell_matches(cell, comparison, value):
    if comparison == "is_null":
        return cell is None
    if comparison == "not_null":
        return cell is not None
    if cell is None:
        return False
    if comparison == "eq":
        return cell == value
    if comparison == "ne":
        return cell != value
    if comparison == "in":
        return cell in value
    if comparison == "not_in":
        return cell not in value
    if comparison == "contains":
        return isinstance(cell, str) and str(value) in cell
    left, right = sort_key(cell), sort_key(value)
    if comparison == "lt":
        return left < right
    if comparison == "lte":
        return left <= right
    if comparison == "gt":
        return left > right
    return left >= right


def filter_(args):
    """the rows matching every (or any) clause. a clause is ``[column, comparison, value]``."""
    table = check(args["table"])
    clauses = args.get("where") or []
    combine = args.get("combine", "and")
    if combine not in ("and", "or"):
        raise ValueError("filter combine must be 'and' or 'or', got %r" % (combine,))
    prepared = []
    for clause in clauses:
        if not isinstance(clause, (list, tuple)) or len(clause) not in (2, 3):
            raise ValueError("a filter clause is [column, comparison, value], got %r" % (clause,))
        name, comparison = clause[0], clause[1]
        if comparison not in COMPARISONS:
            raise ValueError("unknown comparison %r: one of %s" % (comparison, ", ".join(COMPARISONS)))
        if comparison in ("is_null", "not_null"):
            value = None
        elif len(clause) != 3:
            raise ValueError("the comparison %r needs a value" % (comparison,))
        else:
            value = clause[2]
        prepared.append((index_of(table, name), comparison, value))
    negate = bool(args.get("negate", False))
    rows = []
    for row in table["rows"]:
        verdicts = [_cell_matches(row[at], comparison, value)
                    for at, comparison, value in prepared]
        keep = all(verdicts) if combine == "and" else (any(verdicts) if verdicts else True)
        if not verdicts:
            keep = True
        if negate:
            keep = not keep
        if keep:
            rows.append(list(row))
    return make(_for(args, "the rows of %s matching %d clause(s)"
                     % (table.get("for", "a dataset"), len(prepared))),
                table["columns"], rows)


def _aggregate_py(kind, values):
    present = [v for v in values if v is not None]
    if kind == "count":
        return len(present)
    if kind == "count_missing":
        return len(values) - len(present)
    if kind == "nunique":
        return len({sort_key(v) for v in present})
    if kind == "first":
        return present[0] if present else None
    if kind == "last":
        return present[-1] if present else None
    numbers = numeric(present)
    if not numbers:
        return None
    if kind == "sum":
        return math.fsum(numbers)
    if kind == "mean":
        return math.fsum(numbers) / len(numbers)
    if kind == "median":
        ordered = sorted(numbers)
        half = len(ordered) // 2
        return ordered[half] if len(ordered) % 2 else (ordered[half - 1] + ordered[half]) / 2.0
    if kind == "min":
        return min(numbers)
    if kind == "max":
        return max(numbers)
    if len(numbers) < 2:
        return None
    centre = math.fsum(numbers) / len(numbers)
    variance = math.fsum((v - centre) ** 2 for v in numbers) / (len(numbers) - 1)
    return variance if kind == "var" else math.sqrt(variance)


def _aggregate_np(kind, values):
    import numpy as np

    present = [v for v in values if v is not None]
    if kind in ("count", "count_missing", "nunique", "first", "last"):
        return _aggregate_py(kind, values)
    numbers = np.asarray(numeric(present), dtype=float)
    if numbers.size == 0:
        return None
    if kind == "sum":
        return float(numbers.sum())
    if kind == "mean":
        return float(numbers.mean())
    if kind == "median":
        return float(np.median(numbers))
    if kind == "min":
        return float(numbers.min())
    if kind == "max":
        return float(numbers.max())
    if numbers.size < 2:
        return None
    if kind == "var":
        return float(numbers.var(ddof=1))
    return float(numbers.std(ddof=1))


def _aggregate(kind, values, backend):
    if kind not in AGGREGATES:
        raise ValueError("unknown aggregate %r: one of %s" % (kind, ", ".join(AGGREGATES)))
    return _aggregate_np(kind, values) if backend == "np" else _aggregate_py(kind, values)


def group_by(args):
    """one row per distinct key, with the aggregates asked for.

    ``by`` is a list of column names; ``aggregates`` is a list of
    ``{"column", "fn", "as"}``. groups come out in first-seen order unless
    ``sorted`` is true. reference for the numeric aggregates: numpy.
    """
    table = check(args["table"])
    by = args.get("by") or []
    if isinstance(by, str):
        by = [by]
    key_at = [index_of(table, name) for name in by]
    aggregates = args.get("aggregates") or []
    if not aggregates:
        raise ValueError("group_by needs at least one aggregate")
    backend = _backend(args)
    prepared = []
    for spec in aggregates:
        if not isinstance(spec, dict) or "fn" not in spec:
            raise ValueError("an aggregate is {'column', 'fn', 'as'}, got %r" % (spec,))
        kind = spec["fn"]
        if kind not in AGGREGATES:
            raise ValueError("unknown aggregate %r: one of %s" % (kind, ", ".join(AGGREGATES)))
        name = spec.get("column")
        if name is None:
            if kind not in ("count", "count_missing"):
                raise ValueError("the aggregate %r needs a column" % (kind,))
            at = None
        else:
            at = index_of(table, name)
        label = spec.get("as") or ("%s_%s" % (name, kind) if name else kind)
        prepared.append((at, kind, label))
    header = list(by) + [label for _, _, label in prepared]
    if len(set(header)) != len(header):
        raise ValueError("group_by would produce a repeated column name: %r" % (header,))
    order = []
    buckets = {}
    for row in table["rows"]:
        key = tuple(sort_key(row[i]) for i in key_at)
        if key not in buckets:
            buckets[key] = ([row[i] for i in key_at], [])
            order.append(key)
        buckets[key][1].append(row)
    if args.get("sorted"):
        order.sort()
    rows = []
    for key in order:
        label_values, members = buckets[key]
        out = list(label_values)
        for at, kind, _ in prepared:
            values = [len(members)] * len(members) if at is None else [row[at] for row in members]
            if at is None:
                out.append(len(members) if kind == "count" else 0)
            else:
                out.append(_aggregate(kind, values, backend))
        rows.append(out)
    return make(_for(args, "%s grouped by %s" % (table.get("for", "a dataset"), ", ".join(by) or "everything")),
                header, rows)


def join(args):
    """an equi-join of two dataset Parts on one or more key columns.

    ``how``: inner, left, right, outer. key columns keep their name; every other
    clash takes the suffix pair (default ``["_left", "_right"]``).
    """
    left = check(args["table"], "table")
    right = check(args["other"], "other")
    how = args.get("how", "inner")
    if how not in HOWS:
        raise ValueError("join how must be one of %s, got %r" % (", ".join(HOWS), how))
    on = args.get("on")
    if on is None:
        raise ValueError("join needs 'on': a column name, a list of them, or {'left', 'right'}")
    if isinstance(on, str):
        left_keys = right_keys = [on]
    elif isinstance(on, dict):
        left_keys, right_keys = list(on["left"]), list(on["right"])
    else:
        left_keys = right_keys = list(on)
    if len(left_keys) != len(right_keys):
        raise ValueError("join needs the same number of key columns on each side")
    left_at = [index_of(left, name, "left key") for name in left_keys]
    right_at = [index_of(right, name, "right key") for name in right_keys]
    suffixes = args.get("suffixes") or ["_left", "_right"]
    left_rest = [i for i in range(len(left["columns"])) if i not in left_at]
    right_rest = [i for i in range(len(right["columns"])) if i not in right_at]
    clashes = ({left["columns"][i] for i in left_rest}
               & {right["columns"][i] for i in right_rest})
    header = list(left_keys)
    header += [left["columns"][i] + (suffixes[0] if left["columns"][i] in clashes else "")
               for i in left_rest]
    header += [right["columns"][i] + (suffixes[1] if right["columns"][i] in clashes else "")
               for i in right_rest]
    if len(set(header)) != len(header):
        raise ValueError("this join would produce a repeated column name: %r" % (header,))
    index = {}
    for row in right["rows"]:
        index.setdefault(tuple(sort_key(row[i]) for i in right_at), []).append(row)
    rows = []
    matched_right = set()
    for row in left["rows"]:
        key = tuple(sort_key(row[i]) for i in left_at)
        partners = index.get(key, [])
        if partners:
            matched_right.add(key)
            for partner in partners:
                rows.append([row[i] for i in left_at]
                            + [row[i] for i in left_rest]
                            + [partner[i] for i in right_rest])
        elif how in ("left", "outer"):
            rows.append([row[i] for i in left_at]
                        + [row[i] for i in left_rest]
                        + [None] * len(right_rest))
    if how in ("right", "outer"):
        seen = {tuple(sort_key(row[i]) for i in left_at) for row in left["rows"]}
        for row in right["rows"]:
            key = tuple(sort_key(row[i]) for i in right_at)
            if key not in seen:
                rows.append([row[i] for i in right_at]
                            + [None] * len(left_rest)
                            + [row[i] for i in right_rest])
    return make(_for(args, "%s joined to %s on %s (%s)"
                     % (left.get("for", "a dataset"), right.get("for", "another dataset"),
                        ", ".join(left_keys), how)),
                header, rows)


def pivot(args):
    """a long table folded wide: one row per ``index``, one column per value of ``columns``."""
    table = check(args["table"])
    index_columns = args["index"]
    if isinstance(index_columns, str):
        index_columns = [index_columns]
    spread = args["columns"]
    values = args["values"]
    kind = args.get("agg", "sum")
    backend = _backend(args)
    index_at = [index_of(table, name) for name in index_columns]
    spread_at = index_of(table, spread)
    values_at = index_of(table, values)
    heads = []
    order = []
    buckets = {}
    for row in table["rows"]:
        key = tuple(sort_key(row[i]) for i in index_at)
        head = row[spread_at]
        if key not in buckets:
            buckets[key] = ([row[i] for i in index_at], {})
            order.append(key)
        if head not in heads:
            heads.append(head)
        buckets[key][1].setdefault(sort_key(head), []).append(row[values_at])
    heads.sort(key=sort_key)
    header = list(index_columns) + [("" if head is None else str(head)) for head in heads]
    if len(set(header)) != len(header):
        raise ValueError("this pivot would produce a repeated column name: %r" % (header,))
    if args.get("sorted"):
        order.sort()
    rows = []
    for key in order:
        labels, cells = buckets[key]
        out = list(labels)
        for head in heads:
            found = cells.get(sort_key(head))
            out.append(_aggregate(kind, found, backend) if found else args.get("fill"))
        rows.append(out)
    return make(_for(args, "%s pivoted: %s by %s" % (table.get("for", "a dataset"), values, spread)),
                header, rows)


def sort(args):
    """the rows in the order asked for: ``by`` is a list of names or of ``{"column", "descending"}``."""
    table = check(args["table"])
    by = args.get("by")
    if by is None:
        raise ValueError("sort needs 'by'")
    if isinstance(by, str):
        by = [by]
    keys = []
    for spec in by:
        if isinstance(spec, str):
            keys.append((index_of(table, spec), False))
        elif isinstance(spec, dict):
            keys.append((index_of(table, spec["column"]), bool(spec.get("descending", False))))
        else:
            raise ValueError("a sort key is a column name or {'column', 'descending'}, got %r" % (spec,))
    rows = list(table["rows"])
    for at, descending in reversed(keys):
        rows.sort(key=lambda row, at=at: sort_key(row[at]), reverse=descending)
    return make(_for(args, "%s sorted" % table.get("for", "a dataset")), table["columns"],
                [list(row) for row in rows])


def window(args):
    """a window column added beside the rows: cumulative, lag, lead or rank, inside ``partition_by``.

    ``fn``: cumsum, cummean, cummax, cummin, cumcount, lag, lead, rank, dense_rank,
    row_number, share. ``order_by`` orders inside each partition; without it the
    table's own order stands.
    """
    table = check(args["table"])
    kind = args.get("fn", "cumsum")
    known = ("cumsum", "cummean", "cummax", "cummin", "cumcount", "lag", "lead",
             "rank", "dense_rank", "row_number", "share")
    if kind not in known:
        raise ValueError("unknown window fn %r: one of %s" % (kind, ", ".join(known)))
    name = args.get("column")
    needs_column = kind not in ("cumcount", "row_number")
    if needs_column and name is None:
        raise ValueError("the window %r needs a column" % (kind,))
    at = index_of(table, name) if name is not None else None
    partition = args.get("partition_by") or []
    if isinstance(partition, str):
        partition = [partition]
    partition_at = [index_of(table, one) for one in partition]
    order_by = args.get("order_by")
    label = args.get("as") or ("%s_%s" % (name, kind) if name else kind)
    if label in table["columns"]:
        raise ValueError("the window column %r is already in this dataset" % (label,))
    offset = int(args.get("offset", 1))
    positions = list(range(len(table["rows"])))
    if order_by is not None:
        order_at = index_of(table, order_by)
        positions.sort(key=lambda i: sort_key(table["rows"][i][order_at]))
    groups = {}
    for i in positions:
        key = tuple(sort_key(table["rows"][i][j]) for j in partition_at)
        groups.setdefault(key, []).append(i)
    out = [None] * len(table["rows"])
    for members in groups.values():
        values = [table["rows"][i][at] for i in members] if at is not None else []
        if kind in ("cumsum", "cummean", "cummax", "cummin", "share"):
            numbers = numeric(values, "the window column")
            if len(numbers) != len(values):
                raise ValueError("a numeric window cannot run over missing cells")
            running = []
            total = 0.0
            for index, v in enumerate(numbers):
                total += v
                if kind == "cumsum":
                    running.append(total)
                elif kind == "cummean":
                    running.append(total / (index + 1))
                elif kind == "cummax":
                    running.append(max(numbers[: index + 1]))
                elif kind == "cummin":
                    running.append(min(numbers[: index + 1]))
                else:
                    running.append(None)
            if kind == "share":
                whole = math.fsum(numbers)
                if whole == 0.0:
                    raise ValueError("a share window needs a partition that sums to something")
                running = [v / whole for v in numbers]
        elif kind == "cumcount":
            running = list(range(len(members)))
        elif kind == "row_number":
            running = list(range(1, len(members) + 1))
        elif kind == "lag":
            running = [values[i - offset] if i - offset >= 0 else None for i in range(len(values))]
        elif kind == "lead":
            running = [values[i + offset] if i + offset < len(values) else None
                       for i in range(len(values))]
        else:
            ordered = sorted(range(len(values)), key=lambda i: sort_key(values[i]))
            running = [None] * len(values)
            place = 1
            dense = 0
            previous = object()
            for count, i in enumerate(ordered):
                key = sort_key(values[i])
                if key != previous:
                    place = count + 1
                    dense += 1
                    previous = key
                running[i] = place if kind == "rank" else dense
        for i, value in zip(members, running):
            out[i] = value
    rows = [list(row) + [out[i]] for i, row in enumerate(table["rows"])]
    return make(_for(args, "%s with a %s window" % (table.get("for", "a dataset"), kind)),
                list(table["columns"]) + [label], rows)


def missing_report(args):
    """how much of each column is missing, as a json-able mapping."""
    table = check(args["table"])
    total = len(table["rows"])
    counts = {}
    for name in table["columns"]:
        gone = sum(1 for cell in column(table, name) if cell is None)
        counts[name] = {"missing": gone, "present": total - gone,
                        "fraction": (gone / total) if total else 0.0}
    return {"rows": total, "columns": counts,
            "complete_rows": sum(1 for row in table["rows"] if all(c is not None for c in row))}


def missing(args):
    """handle the missing cells: drop rows, or fill by constant, mean, median, forward or backward."""
    table = check(args["table"])
    strategy = args.get("strategy", "drop")
    known = ("drop", "constant", "mean", "median", "forward", "backward")
    if strategy not in known:
        raise ValueError("unknown missing strategy %r: one of %s" % (strategy, ", ".join(known)))
    names = args.get("columns") or list(table["columns"])
    at = [index_of(table, name) for name in names]
    backend = _backend(args)
    rows = [list(row) for row in table["rows"]]
    if strategy == "drop":
        how = args.get("how", "any")
        if how not in ("any", "all"):
            raise ValueError("missing drop how must be 'any' or 'all', got %r" % (how,))
        keep = []
        for row in rows:
            gone = [row[i] is None for i in at]
            if (any(gone) if how == "any" else (all(gone) and gone)):
                continue
            keep.append(row)
        rows = keep
    elif strategy == "constant":
        if "value" not in args:
            raise ValueError("the constant strategy needs a 'value'")
        for row in rows:
            for i in at:
                if row[i] is None:
                    row[i] = args["value"]
    elif strategy in ("mean", "median"):
        for i in at:
            values = [row[i] for row in rows]
            replacement = _aggregate(strategy, values, backend)
            if replacement is None:
                continue
            for row in rows:
                if row[i] is None:
                    row[i] = replacement
    else:
        step = 1 if strategy == "forward" else -1
        for i in at:
            carried = None
            for row in (rows if step == 1 else reversed(rows)):
                if row[i] is None:
                    if carried is not None:
                        row[i] = carried
                else:
                    carried = row[i]
    return make(_for(args, "%s with missing cells handled by %s"
                     % (table.get("for", "a dataset"), strategy)),
                table["columns"], rows)


def shape(args):
    """the shape of a dataset Part, and what each column holds."""
    table = check(args["table"])
    kinds = {}
    for name in table["columns"]:
        cells = column(table, name)
        present = [c for c in cells if c is not None]
        if not present:
            kinds[name] = "empty"
        elif all(isinstance(c, bool) for c in present):
            kinds[name] = "boolean"
        elif all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in present):
            kinds[name] = "number"
        elif all(isinstance(c, str) for c in present):
            kinds[name] = "text"
        else:
            kinds[name] = "mixed"
    return {"rows": len(table["rows"]), "columns": list(table["columns"]), "kinds": kinds}


SELECT = Calculation("fn.brain.data.select", select)
FILTER = Calculation("fn.brain.data.filter", filter_)
GROUP_BY = Calculation("fn.brain.data.group_by", group_by)
JOIN = Calculation("fn.brain.data.join", join)
PIVOT = Calculation("fn.brain.data.pivot", pivot)
SORT = Calculation("fn.brain.data.sort", sort)
WINDOW = Calculation("fn.brain.data.window", window)
MISSING = Calculation("fn.brain.data.missing", missing)
MISSING_REPORT = Calculation("fn.brain.data.missing_report", missing_report)
SHAPE = Calculation("fn.brain.data.shape", shape)

CALCS = {
    c.address: c
    for c in (SELECT, FILTER, GROUP_BY, JOIN, PIVOT, SORT, WINDOW, MISSING,
              MISSING_REPORT, SHAPE)
}
