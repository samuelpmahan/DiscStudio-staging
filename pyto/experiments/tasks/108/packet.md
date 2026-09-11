# Task 108

Intent: brain kerchoo: the owner's speed pass across all four verticals - the loops hiding inside vectorised engines (an sp or np engine that called scipy or numpy once per element is one vectorised call now), backend=auto as the default when a caller names no engine, the plan Part extended to the stats, data and ml calcs that have bench Parts, and one Part px.exp.brain.bench.kerchoo recording before, after, speedup and the engine chosen for every calc touched
Starting point: 7e2e2cf6c9056a67cea6287ed628f55b8975c2e3 (land(task-107): brain/stats and brain/data close the night: the empirical cdf and its quantile inverse against scipy.stats.ecdf, and the two findings this vertical owes the backend vertical -- what stats and data each had to do by hand because the facade has no op for it, with the workaround taken and the op proposed)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} both runs are in the packet: the copy's venv (python 3.11, numpy 2.4.6) through the Verify
line and python 3.12.3 / numpy 2.5.3 / scipy 1.18.1 at
experiments/tasks/108/evidence/verify-python312-numpy253.txt. 756 tests, OK in both, and every
oracle Part still passes except the three deliberate py_gram_unguarded ones.
{?} nothing here changes an answer. The stats sp engine now calls scipy ONCE over the array
instead of once per element - the same function on the same numbers - and data's np rolling engine
takes the prefix-sum path for the kinds that have one, which is the code its own cumsum engine
already ran and its own oracle Parts already cover.
{?} the backend facade now defaults to the plan when the caller names no engine. The plan is read
from the committed store ONCE as module data, never inside a call, so a Calculation is still a pure
function of its inputs plus a constant table. "py" still names the reference engine, args["plan"]
still overrides, and an op the plan says nothing about falls back to py.
{?} what this pass did NOT reach, recorded as proposal.brain.backend.the_pass_reached_the_loops_not_the_facades:
ml.knn_predict (524 ms) and ml.softmax_fit (467 ms) are pure-python calculations running on py
because the stats, data and ml facades have no plan to read. Giving them the same default-to-the-plan
dispatch is a change to three dispatchers and did not fit the window. The proposal is one shared
chooser in harness.py that every facade calls.
{?} px.exp.brain.bench.kerchoo holds the table. `before` is read out of the committed benchmark
Parts rather than retyped; `after` is the minimum of five runs on this machine, so the speedups are
this machine's.
