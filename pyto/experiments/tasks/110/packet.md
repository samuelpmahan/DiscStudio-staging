# Task 110

Intent: brain/ml the kerchoo slice: the ml facade defaults to the plan instead of to py - ml/core.py's dispatch reads px.exp.brain.result.backend.plan when the caller names no engine, the plan is extended to the ml calcs that have bench Parts, py stays the reference and is still selectable by name - with knn_predict and softmax_fit re-benched and their rows appended to px.exp.brain.bench.kerchoo, and a finding for every ml calc that has no faster engine to choose
Starting point: 7cc30b68d957e318209260f395a9594a0b613ae7 (land(task-109): brain: the blok generation lane, filed as a Part - proposal.brain.blok_generation, a seeded motif-patterned variation over the brain's Calculations through crisp vary, judged by the oracle Parts for correct, the benchmark Parts for fast and neat delta for cheap, with the winners' recurring motifs mined back into the motif set; and the same as a next entry on the backend map Part)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} both runs are in the packet: the copy's venv and python 3.12.3 / numpy 2.5.3 / scipy 1.18.1 at
experiments/tasks/110/evidence/verify-python312-numpy253.txt. 756 tests, OK in both, every oracle
passing except the three deliberate py_gram_unguarded ones.
{?} `core.backend_of({})` is still "py". A calculation opts into the plan by passing its own
benchmark name - `core.backend_of(args, calc="knn_predict")` - so the change is visible at each
call site rather than hidden in the default, and the ml vertical's existing test that pins
backend_of({}) == "py" still says something true.
{?} six ml calcs are wired: knn_predict, softmax_fit, linreg_fit, logreg_fit, silhouette,
lasso_fit. logreg_fit's fastest recorded name is `newton-np`, which is not in the engine list its
facade validates, so the chooser ignores it and logreg_fit stays on py - that is
proposal.brain.backend.a_plan_may_only_name_an_engine_the_facade_has, with ml.pairwise, ml.tree_fit
and ml.kmeans in the same shape. The plan naming an engine a facade cannot run is ignored, never
obeyed, so a stale plan can only cost speed and never correctness.
{?} the plan now carries `by_calc` for 47 calcs across stats, data and ml, keyed "<vertical>.<calc>".
Their size tokens are each vertical's own words and cannot be turned into an element count the way
the backend's can, so what is recorded is the engine fastest at the largest recorded case and the
spread it won by - a facade with no size to reason about still gets the right default, but it
cannot switch engine with n the way the backend ops do.
{?} the kerchoo Part now has 12 rows. `before` is read out of the committed benchmark Parts;
`after` is the minimum of five runs on this machine.
