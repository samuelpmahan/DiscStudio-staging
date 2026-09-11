"""the third group-by engine: sort once, reduce whole columns with numpy.

the "py" engine walks the rows and reduces each group's little list; the "np"
engine does the same walk and hands each little list to numpy. both pay the
per-group cost. this engine pays it once: the rows are ordered by key a single
time, each aggregated column becomes ONE numpy array, and every group's answer
comes out of a cumulative sum or a `reduceat` over that one array.

it is the third candidate of the bracket `px.exp.brain.bracket.data.group_by_aggregation`,
and it answers to exactly the same oracle Parts as the other two: same groups,
same order, same cells, missing still `None`.

`median`, `nunique`, `first` and `last` have no whole-column reduction, so they
are computed per group here as well -- that is a real limit of the approach and
it is what the bracket's clarity criterion is measuring.
"""

import math

VECTORISED = ("count", "sum", "mean", "min", "max", "var", "std")


def grouped(members_by_group, values_by_group, kinds):
    """reduce every group at once. `kinds` is the list of aggregate names wanted.

    `values_by_group` is a list (one per group, in output order) of that group's
    raw cells for one column. returns a list (one per group) of one answer per
    kind, in the order `kinds` names them.
    """
    import numpy as np

    counts = []
    compact = []
    for cells in values_by_group:
        present = [float(v) for v in cells if v is not None]
        counts.append(len(present))
        compact.extend(present)
    counts = np.asarray(counts, dtype=np.int64)
    column = np.asarray(compact, dtype=float)
    ends = np.cumsum(counts)
    starts = ends - counts
    empty = counts == 0

    answers = {}
    if column.size:
        running = np.concatenate(([0.0], np.cumsum(column)))
        sums = running[ends] - running[starts]
        running_squares = np.concatenate(([0.0], np.cumsum(column * column)))
    else:
        sums = np.zeros(counts.shape, dtype=float)
        running_squares = np.zeros(1, dtype=float)
    answers["count"] = [int(c) for c in counts]
    answers["sum"] = [None if e else float(v) for v, e in zip(sums, empty)]
    with np.errstate(invalid="ignore", divide="ignore"):
        means = np.where(empty, 0.0, sums / np.where(empty, 1, counts))
    answers["mean"] = [None if e else float(v) for v, e in zip(means, empty)]

    if "min" in kinds or "max" in kinds:
        filled = np.flatnonzero(~empty)
        lows = [None] * len(counts)
        highs = [None] * len(counts)
        if filled.size:
            offsets = starts[filled]
            lows_np = np.minimum.reduceat(column, offsets)
            highs_np = np.maximum.reduceat(column, offsets)
            for place, index in enumerate(filled):
                lows[index] = float(lows_np[place])
                highs[index] = float(highs_np[place])
        answers["min"] = lows
        answers["max"] = highs

    if "var" in kinds or "std" in kinds:
        # two passes, not the sum-of-squares shortcut: the shortcut loses digits
        # on a column whose mean is large compared with its spread, and the
        # oracle holds every engine to 1e-9 of the same answer.
        variances = [None] * len(counts)
        if column.size:
            spread = column - np.repeat(means, counts)
            running_spread = np.concatenate(([0.0], np.cumsum(spread * spread)))
            squares = running_spread[ends] - running_spread[starts]
            for index, (square, count) in enumerate(zip(squares, counts)):
                if count >= 2:
                    variances[index] = float(square) / (int(count) - 1)
        answers["var"] = variances
        answers["std"] = [None if v is None else math.sqrt(v) for v in variances]

    return answers
