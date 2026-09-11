# Task 92

Intent: brain/stats and brain/data build the Parts: every oracle, benchmark, dataset, result and record this vertical owns, persisted to store/stats.json and store/data.json, the two tournaments (OLS normal equations against householder QR against numpy lstsq, and group-by aggregation py against np) with their criteria written down before any judging and scored by a referee that built neither, the findings, and the map Parts px.exp.brain.map.stats and px.exp.brain.map.data
Starting point: 804252504b559b1eee36c062ea00a9a5781ddb87 (land(task-91): brain harness (and the one line of ml/parts.py that is the same bug): a Store writes its store and records into a temporary directory unless it is an explicit record run (Store(commit=True), or BRAIN_RECORDS=commit), so no test can rewrite a tracked run record - a wall-clock duration inside a committed file leaves MAIN dirty and land.sh then refuses the NEXT landing, for whoever lands next rather than for whoever wrote it; reading is unchanged, load_store() still reads the committed store)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
