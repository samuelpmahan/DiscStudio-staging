# Task 109

Intent: brain: the blok generation lane, filed as a Part - proposal.brain.blok_generation, a seeded motif-patterned variation over the brain's Calculations through crisp vary, judged by the oracle Parts for correct, the benchmark Parts for fast and neat delta for cheap, with the winners' recurring motifs mined back into the motif set; and the same as a next entry on the backend map Part
Starting point: a6d6ae5ac0b422b867259a1b8fb26f4fba77a937 (land(task-108): brain kerchoo: the owner's speed pass across all four verticals - the loops hiding inside vectorised engines (an sp or np engine that called scipy or numpy once per element is one vectorised call now), backend=auto as the default when a caller names no engine, the plan Part extended to the stats, data and ml calcs that have bench Parts, and one Part px.exp.brain.bench.kerchoo recording before, after, speedup and the engine chosen for every calc touched)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/backend/summary.py
- M  pyto/experiments/brain/store/backend.json

```
pyto/experiments/brain/backend/summary.py | 25 +++++++++++++++++++++++++
 pyto/experiments/brain/store/backend.json | 11 +++++++++++
 2 files changed, 36 insertions(+)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.uTbZi9Lhfe) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               756  OK
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

{?} both runs are in the packet: the copy's venv and python 3.12.3 / numpy 2.5.3 / scipy 1.18.1 at
experiments/tasks/109/evidence/verify-python312-numpy253.txt. 756 tests, OK in both.
{?} proposal.brain.blok_generation sits at proposal.brain.<k>, not proposal.brain.<vertical>.<k>.
It is a lane about what the whole brain is now good for, not one vertical's finding, so it is
written with store.put rather than harness.finding. If the contract would rather every proposal be
owned by a vertical, this is the one to move.
{?} nothing here changes a Calculation, an engine or an answer. The only source change is
backend/summary.py; the store moves because it was rebuilt over it.
{?} the lane is filed, not started. The first thing it needs is the cross-kind PQL join that three
verticals filed independently tonight - joining px.exp.brain.oracle.* to px.exp.brain.bench.* on
(vertical, calc, case) - which is why that proposal is named from inside this one.
