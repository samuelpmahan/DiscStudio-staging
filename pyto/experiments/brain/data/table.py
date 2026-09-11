"""the dataset shape this vertical reads and writes, and the small helpers over it.

a table Part is ``{"for": ..., "columns": [...], "rows": [[...], ...]}``: json-able
only, so a record, a digest and a replay all work on it unchanged. missing is
``None`` -- never ``float("nan")``, which json cannot hold.
"""


def check(table, what="table"):
    """raise unless ``table`` is the dataset shape, and return it."""
    if not isinstance(table, dict):
        raise ValueError("%s must be a dataset Part (a mapping), got %s" % (what, type(table).__name__))
    for key in ("columns", "rows"):
        if key not in table:
            raise ValueError("%s is missing %r; a dataset Part has 'columns' and 'rows'" % (what, key))
    columns = table["columns"]
    if not isinstance(columns, (list, tuple)) or any(not isinstance(c, str) for c in columns):
        raise ValueError("%s columns must be a list of names" % what)
    if len(set(columns)) != len(columns):
        raise ValueError("%s has a repeated column name: %r" % (what, columns))
    width = len(columns)
    for index, row in enumerate(table["rows"]):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError(
                "%s row %d has %s cells, the header has %d"
                % (what, index, len(row) if isinstance(row, (list, tuple)) else "no", width))
    return table


def index_of(table, column, what="column"):
    """the position of ``column``, or a message naming what is actually there."""
    columns = list(table["columns"])
    if column not in columns:
        raise ValueError("no %s %r in this dataset: %r" % (what, column, columns))
    return columns.index(column)


def column(table, name):
    """one column as a plain list, in row order."""
    at = index_of(table, name)
    return [row[at] for row in table["rows"]]


def make(for_, columns, rows):
    """a dataset Part from a header and rows, checked."""
    return check({"for": for_, "columns": list(columns), "rows": [list(r) for r in rows]})


def numeric(values, what="column"):
    """the non-missing values as floats; anything unconvertible names itself."""
    out = []
    for v in values:
        if v is None:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("%s holds %r, which is not a number" % (what, v))
        out.append(float(v))
    return out


def sort_key(value):
    """a total order over mixed json cells: missing first, then numbers, then strings."""
    if value is None:
        return (0, 0.0, "")
    if isinstance(value, bool):
        return (1, float(value), "")
    if isinstance(value, (int, float)):
        return (1, float(value), "")
    return (2, 0.0, str(value))


def canonical(value, digits=12):
    """every float in a value rounded to ``digits`` significant digits.

    a committed store document is a claim about a calculation, not about the
    machine that ran it: a fresh build on another BLAS, another numpy or another
    python differs in the last bit or two of a float, and a byte comparison of
    the two documents then fails for no reason anybody cares about. twelve
    significant digits is far inside every tolerance this vertical records
    (1e-9 relative, 1e-7 for the one case that says why) and far outside that
    noise, so rounding there makes the document reproducible without making it
    less true. walks dicts and lists; leaves ints, bools, strings and None alone.
    """
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")) or value == 0.0:
            return value
        import math

        exponent = math.floor(math.log10(abs(value)))
        return round(value, max(0, digits - 1 - exponent)) if exponent < digits else \
            float(round(value, 0))
    if isinstance(value, dict):
        return {key: canonical(inner, digits) for key, inner in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical(inner, digits) for inner in value]
    return value
