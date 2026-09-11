# Task 98

Intent: brain/backend and harness, portable across numpy builds: eig's np engine guards on the values and not on the dtype (numpy hands back complex128 for any non-symmetric input, with zero imaginary parts when the spectrum is real, and which numpy you have decides whether it bothers), the pairwise tournament gets a cancelling case built to have no significant digits left rather than a random draw that only fails on some BLAS, and a store is written with every float rounded to twelve significant digits so a committed document is not bit-exact to one machine's arithmetic; verified under this repository's numpy 2.4.6 and under python 3.12 with numpy 2.5.3 and scipy 1.18.1, both runs in the packet
Starting point: 772c8603cf7f3744f9edbd4c3a431d6f31700a3c (land(task-97): brain/stats and brain/data, the third wave: kruskal-wallis, levene and bartlett, the exact binomial test and fisher exact on a 2x2, and the multiple-comparison corrections (bonferroni, holm, benjamini-hochberg) as Calculations with scipy named as the reference; and the column transforms a real pipeline needs: standardise, normalise, rank and bin a column, crosstab two, drop duplicates, concatenate two tables, flag outliers by IQR and by z-score, and oc.brain.data.sample which draws its rows through the effects handle)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 5 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/backend/ops.py
- M  pyto/experiments/brain/backend/test_tournament.py
- M  pyto/experiments/brain/backend/tournament.py
- M  pyto/experiments/brain/harness.py
- M  pyto/experiments/brain/store/backend.json

```
pyto/experiments/brain/backend/ops.py             |    17 +-
 pyto/experiments/brain/backend/test_tournament.py |    26 +-
 pyto/experiments/brain/backend/tournament.py      |    32 +-
 pyto/experiments/brain/harness.py                 |    28 +-
 pyto/experiments/brain/store/backend.json         | 27016 ++++++++++----------
 5 files changed, 13703 insertions(+), 13416 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.uEml2hofxm) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               613  OK
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

{?} the second interpreter's run is committed at experiments/tasks/98/evidence/verify-python312-numpy253.txt
(python 3.12.3, numpy 2.5.3, scipy 1.18.1). Every backend and harness test passes there and here.
One test in it is still red and it is not this vertical's: ml.test_store
TheCommittedStore.test_the_saved_document_matches_a_fresh_build, on
px.exp.brain.data.ml.counts - a committed document compared bit for bit against a fresh build.
That is the same canonical-float rule this task applies to harness.Store.save, applied to
ml/parts.py's own save/document, and it is the ml vertical's to make.
{?} twelve significant digits on save is a choice about where to cut: it is five orders of
magnitude past the loosest tolerance any oracle here uses (1e-7) and comfortably past the bits that
move between numpy builds. It applies to the file only - `put` and `get` keep the full float, and
an oracle compares the full value - so nothing a Calculation computes is rounded.
{?} eig's np engine now returns a real spectrum when the imaginary parts are below 1e-9 of the
spectrum's scale, and refuses above it. That threshold is a judgement: a matrix with a genuinely
tiny but non-zero imaginary spectrum will come back real. The py engine still refuses every
non-symmetric matrix, so the two engines answer different questions there by design, and the map
records it as a stub.
{?} the pairwise tournament's `cancelling` case is three points a million from the origin and a
millionth apart. The unguarded gram expansion is wrong on it in float64 whatever BLAS is
underneath; whether it is also wrong on a random draw is a property of the machine, which is why
the test no longer asks that. The per-size oracle Parts are still written - they are measurements -
and the map may now print two failed oracles on one machine and four on another.
