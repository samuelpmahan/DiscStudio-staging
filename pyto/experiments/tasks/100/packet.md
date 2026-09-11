# Task 100

Intent: brain/backend the benchmark Parts are what decides: the vertical's benchmark Parts are folded through PQL into one Part, px.exp.brain.result.backend.plan, and fn.brain.backend.<op> takes backend=auto, which reads the plan at the size this invocation actually has - still one pure Calculation, because the plan is an input like any other and an auto with no plan is refused by name rather than quietly given numpy; the plan is worth reading: cumsum is fastest in pure python at every size measured, argsort changes engine at the largest one and eig and fft change at the middle
Starting point: 6d29ac32d88cd0a2814eb96cea9ebd30db1e32c1 (land(task-95): brain ml distances: the four calculations that each built their own n-by-n matrix (knn_predict, silhouette, kmeans, dbscan) route through fn.brain.backend.pairwise as one more backend, oracled against their own spelling and against scipy cdist, with the bracket that decides which spelling deserves the default; and exp/88 is killed, its candidate having landed inside task-89)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} both runs are in the packet: the copy's venv (python 3.11, numpy 2.4.6) through the Verify
line, and python 3.12.3 with numpy 2.5.3 and scipy 1.18.1 at
experiments/tasks/100/evidence/verify-python312-numpy253.txt. 673 tests, OK in both - the whole
brain suite, not only this vertical's.
{?} the plan is measured on THIS machine. A slower or faster host, or a numpy built against a
different BLAS, would measure different crossovers and the committed plan Part would be wrong for
it. That is why `choose.build(store)` is a function anyone can re-run rather than a table anyone
typed, and why the map's next list asks for the plan to be rebuilt where it runs.
{?} `backend="auto"` needs `args["plan"]`. Reading the plan off disk inside the facade would have
been friendlier and would have made `fn.brain.backend.<op>` an effect, so it is refused by name
instead. The cost is that every caller who wants auto has to carry one more Part.
{?} the plan only decides at sizes where every engine of an op was measured; a partially measured
size is skipped rather than guessed at. With three engines everywhere today, that skips nothing.
{?} the plan is worth reading before anyone hard-codes numpy: cumsum is fastest in PURE PYTHON at
all three measured sizes (1.2-1.4x), because numpy's per-call overhead is most of the measurement
and the op is one pass either way. argsort, cholesky, eig and fft each change engine between their
three sizes.
