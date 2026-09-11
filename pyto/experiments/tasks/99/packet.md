# Task 99

Intent: brain/stats and brain/data, the fourth wave: the robust summaries (trimmed mean, winsorised sample, median absolute deviation, geometric and harmonic mean, entropy and a histogram) against scipy; a third rolling engine that runs the whole window in one cumulative pass instead of one slice per point, entered as the candidates of a third tournament with its criteria written down first; exponentially weighted moving statistics and the cross-correlation of two series
Starting point: 1fcfbbd858898cf141f92b9080ac1df398258603 (board: **started** `task-98`: brain/backend and harness, portable across numpy)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} Two stacks, not one: evidence/verify-py312.txt is the same suite on python 3.12.3 + numpy
2.5.3 + scipy 1.18.1 as well as the copy's own venv. Every stats and data test passes on both.
The three failures that stack shows are in the backend and ml verticals and were already there.
{?} Three tournaments now, all re-runnable from the store: ols_solver (lstsq), group_by_aggregation
(npsort) and rolling_window (cumsum). The rolling bracket's winner is NOT the facade default and
the refinement note says why: cumsum has no whole-window form for min, max or median and refuses
them, so the default has to be the engine that answers every fn.
{?} Committed documents are canonicalised to twelve significant digits before saving, so a fresh
build on another BLAS saves the same document; the wall-clock fields of a benchmark Part are a
measurement of this machine and are not expected to reproduce.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
