# Task 101

Intent: brain/stats and brain/data, the last wave: the robust simple regressions (theil-sen and siegel repeated medians) and the whole simple-regression verdict in one Calculation, all against scipy; and the three series transforms a pipeline still wants: percentage change, the expanding (whole-history) statistics on the same cumulative pass as the rolling ones, and linear interpolation over the holes
Starting point: c84c961a82c757bd0fa2f37a654b8108bac75ffb (board: **started** `task-100`: brain/backend the benchmark Parts are what decid)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} Two stacks: evidence/verify-py312.txt is the whole brain suite on python 3.12.3 + numpy
2.5.3 + scipy 1.18.1 as well as the copy's own venv. Both are green (693 tests).
{?} fn.brain.data.expanding is fn.brain.data.rolling with the window set to the length of the
series, and nothing else: the same three engines, the same oracle shape, and the cumsum engine
is what turns an expanding statistic from O(n^2) into O(n).
{?} theil_sen reproduces scipy's confidence interval exactly, including the two rank indices
scipy takes from Sen (1968) equation 2.6 -- the interval is part of the oracle, not just the slope.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
