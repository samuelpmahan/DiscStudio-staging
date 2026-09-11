# Task 91

Intent: brain harness (and the one line of ml/parts.py that is the same bug): a Store writes its store and records into a temporary directory unless it is an explicit record run (Store(commit=True), or BRAIN_RECORDS=commit), so no test can rewrite a tracked run record - a wall-clock duration inside a committed file leaves MAIN dirty and land.sh then refuses the NEXT landing, for whoever lands next rather than for whoever wrote it; reading is unchanged, load_store() still reads the committed store
Starting point: a4db7c65fe9b7376574412a3cc13f298f0e16663 (land(task-85): brain/data dataframe-like Calculations fn.brain.data.* over the columns/rows dataset shape: select project filter group-by with aggregates join pivot sort window/rolling and missing-value handling, with py and np backends where the shape pays, dataset Parts px.exp.brain.data.* and oc.brain.data.load that reads csv and json through the effects handle's read_text)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} this task changes three files in pyto/experiments/brain: harness.py (the shared Store), and
ml/parts.py + ml/build.py, which are the ml vertical's own separate Store. Crossing that boundary
was not the plan. The reason: pyto/experiments/brain/ml/parts.py `Store.run` wrote its run record
into the tracked records/ unconditionally, so `build.build(save=False)` - which the ml tests call -
rewrote records/ml.regression.json on every suite run, including the check_all that land.sh runs on
MAIN inside a landing. land.sh then stops at step 5 with "the tree changed while the suites ran".
That refused five landings tonight across three verticals (tasks 85, 87 twice, 88 twice), including
the ml vertical's own, and no vertical could land anything until it was fixed. The change is the
same one the harness gets and preserves the explicit run: `python -m experiments.brain.ml.build`
still writes the committed record (build(save=True) passes commit=True); a test writes a tempdir.
{?} reading and writing now default to different places: `load_store()` still reads the committed
`store/`, `save()` and `run()` write a temporary directory unless Store(commit=True) or
BRAIN_RECORDS=commit. That asymmetry is deliberate - a vertical must see the others' Parts without
being able to overwrite the repository from a test - but `Store().save("backend")` now returns a
path under /tmp and nothing warns. The path is returned; read it rather than assuming.
{?} ml/parts.py `save()` is left alone: it writes store/ml.json unconditionally, and only
build(save=True) calls it, so no test rewrites it today. If a test ever calls it, it will dirty
MAIN the same way.
{?} BRAIN_RECORDS is read at Store construction, not cached at import, so a test may set and unset
it around a block. An explicit commit= flag beats the environment either way.
