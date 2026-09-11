# Task 97

Intent: brain/stats and brain/data, the third wave: kruskal-wallis, levene and bartlett, the exact binomial test and fisher exact on a 2x2, and the multiple-comparison corrections (bonferroni, holm, benjamini-hochberg) as Calculations with scipy named as the reference; and the column transforms a real pipeline needs: standardise, normalise, rank and bin a column, crosstab two, drop duplicates, concatenate two tables, flag outliers by IQR and by z-score, and oc.brain.data.sample which draws its rows through the effects handle
Starting point: e755e1ab96998f1a3b2b580500fe9e50bfc6e094 (board: **started** `task-96`: brain/backend five more ops, one of them the brac)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 16 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/data/build.py
- M  pyto/experiments/brain/data/table.py
- A  pyto/experiments/brain/data/test_canonical.py
- A  pyto/experiments/brain/data/test_transform.py
- A  pyto/experiments/brain/data/transform.py
- A  pyto/experiments/brain/data/transform_cases.py
- M  pyto/experiments/brain/records/data.pipeline.json
- M  pyto/experiments/brain/records/stats.analysis.json
- M  pyto/experiments/brain/stats/build.py
- A  pyto/experiments/brain/stats/comparisons.py
- A  pyto/experiments/brain/stats/comparisons_cases.py
- A  pyto/experiments/brain/stats/test_comparisons.py
- M  pyto/experiments/brain/stats/test_tolerance.py
- M  pyto/experiments/brain/stats/tolerance.py
- M  pyto/experiments/brain/store/data.json
- M  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/build.py               |   27 +-
 pyto/experiments/brain/data/table.py               |   29 +
 pyto/experiments/brain/data/test_canonical.py      |   27 +
 pyto/experiments/brain/data/test_transform.py      |  228 +
 pyto/experiments/brain/data/transform.py           |  324 +
 pyto/experiments/brain/data/transform_cases.py     |  217 +
 pyto/experiments/brain/records/data.pipeline.json  |   10 +-
 pyto/experiments/brain/records/stats.analysis.json |   12 +-
 pyto/experiments/brain/stats/build.py              |   13 +-
 pyto/experiments/brain/stats/comparisons.py        |  282 +
 pyto/experiments/brain/stats/comparisons_cases.py  |  140 +
 pyto/experiments/brain/stats/test_comparisons.py   |  169 +
 pyto/experiments/brain/stats/test_tolerance.py     |   28 +-
 pyto/experiments/brain/stats/tolerance.py          |   29 +
 pyto/experiments/brain/store/data.json             | 6634 ++++++++++++--------
 pyto/experiments/brain/store/stats.json            | 6276 ++++++++++--------
 16 files changed, 9114 insertions(+), 5331 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.fAr3AclPeX) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               612  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK

## Uncertain

{?} Two stacks, not one: evidence/verify-py312.txt is the same suite on python 3.12.3 + numpy
2.5.3 + scipy 1.18.1 as well as the copy's own venv. Every stats and data test passes on both.
The three failures that stack shows (backend.test_ops eig, backend.test_tournament gram,
ml.test_store saved-document) are in other verticals and were already there.
{?} Committed documents: store/stats.json and store/data.json are written through a
canonicalisation that rounds every float to twelve significant digits (stats.tolerance.canonical,
data.table.canonical), so a fresh build on another BLAS saves the same document. The wall-clock
fields of a benchmark Part are a measurement of this machine and are not expected to reproduce.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
