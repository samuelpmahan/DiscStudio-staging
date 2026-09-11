# Task 104

Intent: brain/stats and brain/data, closing two named stubs: weighted least squares through the same three solvers the tournament judged, with the weights in the design rather than in a fourth solver, and its oracle against numpy.linalg.lstsq on the scaled design; and the as-of (rolling) join, the one join a time series actually wants, backward forward or nearest with a tolerance
Starting point: f33b9e5f3111932ccfd091bc8a2d723a7aafecb8 (board: **started** `task-103`: brain/backend six more primitives and the case t)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} Two stacks, both green (736 tests): evidence/verify-py312.txt is the whole brain suite on
python 3.12.3 + numpy 2.5.3 + scipy 1.18.1 as well as the copy's own venv.
{?} Two named stubs close here, and the map says so: fn.brain.stats.ols_weighted and
fn.brain.data.rolling_join both come off px.exp.brain.map.stats/.data's stubbed list, and the
'next' entries that pointed at them now point at what is left behind them (a huber m-estimator
over the weighted fit; a calendar-aware index under the as-of join).
{?} The weights go into the DESIGN, not into a fourth solver: ols_weighted scales each row by
sqrt(w) and calls whichever of the three tournament solvers is named, so the bracket's answer
still holds for the weighted case and there is nothing new to judge.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
