# Task 68

Intent: the first batch through the integrated loop: neat ask run once on the tree that holds tasks 65, 66 and 67 together, its batch Part and run record kept as evidence under pyto/experiments/review; FRONTIER.md's Landed adds gain the three (the question loop, the difference before it is shown with counting before mining, the join's gate) in the owner's words
Starting point: dfd020b77d3fb1e46c4c0274712fd80261d51b8d (land(task-66): the difference is computed before it is shown, and counting comes before mining: pyto/src/pyto/neat/diff.py registers fn.neat.diff.candidates (two PQL documents and a seed store in, px.exp.blok.diff.<a>.<b> out: structural same or different, each output same, changed or new by value digest, and the remainder no calculation settled; documents with oc. calls are not run and say so); neat diff prints it and keeps the Part under pyto/experiments/review/diffs; pyto/experiments/molecules/transitions.py registers fn.molecules.transitions (every run record's invocation-to-invocation and Part-to-invocation transition counted, px.exp.molecules.transitions, stable order) and report.md opens with the count table before any molecule)
Verify: cd pyto && test -s experiments/review/batches/2.json && python -m unittest tests.test_neat_review tests.test_neat_diff tests.test_neat_gate && grep -q 'task 67' FRONTIER.md
Allow: pyto/experiments/review pyto/FRONTIER.md pyto/experiments/tasks
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/FRONTIER.md
- A  pyto/experiments/review/batches/2.json
- A  pyto/experiments/review/runs/ask-2.json

```
pyto/FRONTIER.md                        |   23 +
 pyto/experiments/review/batches/2.json  | 1955 +++++++++++++++++++++++++++++++
 pyto/experiments/review/runs/ask-2.json | 1467 +++++++++++++++++++++++
 3 files changed, 3445 insertions(+)
```

## Evidence

- verify: `cd pyto && test -s experiments/review/batches/2.json && python -m unittest tests.test_neat_review tests.test_neat_diff tests.test_neat_gate && grep -q 'task 67' FRONTIER.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.iBKg1NNRzo) (evidence/check_all.txt)
    suite                         tests  status
    library                         366  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} RootLabelsCountAsOpen: batch 2 holds 278 items and 117 of them are labels already on pyto/questions.md, most with a decision in prose under them; the collator counts a root label as open until an answer file exists for it. Whether a root entry with an Owner line or a Decided line is already answered is the owner's to say; until then the batch is long.
