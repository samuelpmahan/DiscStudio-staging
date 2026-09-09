# Task 17

Intent: cross-project hit: a second tiny domain reads the same per-user materials store and gets a verified hit on material the ablation experiment produced, with counters and a receipt
Starting point: 12c65281bf9999f5d44ff5b1b883594ca9d5cdb0 (proof: fresh clone on D:/ after task 15)
Verify: P=.venv/bin/python; [ -x "$P" ] || P=.venv/Scripts/python.exe; "$P" -m unittest discover -s pyto/experiments/cross-project -q
Allow: pyto/experiments/cross-project pyto/scripts/check_all.sh
Candidate: 6 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/cross-project/evidence/run-1/counters.json
- A  pyto/experiments/cross-project/evidence/run-1/cross-project-ledger.json
- A  pyto/experiments/cross-project/evidence/run-1/interpretation.md
- A  pyto/experiments/cross-project/program.py
- A  pyto/experiments/cross-project/run.py
- A  pyto/experiments/cross-project/test_cross_project.py

```
.../cross-project/evidence/run-1/counters.json     |   6 +
 .../evidence/run-1/cross-project-ledger.json       |  62 ++++
 .../cross-project/evidence/run-1/interpretation.md |  25 ++
 pyto/experiments/cross-project/program.py          | 143 +++++++++
 pyto/experiments/cross-project/run.py              | 318 +++++++++++++++++++++
 .../cross-project/test_cross_project.py            | 219 ++++++++++++++
 6 files changed, 773 insertions(+)
```

## Evidence

- verify: `P=.venv/bin/python; [ -x "$P" ] || P=.venv/Scripts/python.exe; "$P" -m unittest discover -s pyto/experiments/cross-project -q` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    240  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           87  OK
    viewer-record-schema             19  OK
    

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

`{?} PrivateHelperImport`: pyto/experiments/cross-project/program.py and run.py import `pyto.pcr`'s
underscore-prefixed `_implementation_sha256`/`_result_sha256` directly (not experiment-local, not
reimplemented) so the shared revision and digest are guaranteed identical to what the ablation
domain's own receipts recorded -- the alternative was recomputing the same formula independently,
which risks drift. Should pyto expose these as a small public digest API (e.g. on `Calculation` or
as module functions in `pyto`) instead of leaving experiments to reach into `pcr.py`'s internals?

`{?} OneSharedMaterialIsEnough`: this experiment demonstrates exactly one shared material
(`fn.ablation.split` on the seed-7, n=400 fixture) verified hit between two domains. Is one
address/Calculation shared and hit enough to move `{?} CrossProjectReuse` from open to resolved, or
does the thesis (Reframing 3: "a per-user engram table... reusable per user across projects") need
more than one shared address, or a second consumer beyond this task's purpose-built fixture, before
the cross-project claim counts as verified rather than merely demonstrated once?

`{?} DefaultStoreRootStillPerUser`: run.py's CLI defaults to a fresh temporary materials store
(never the real per-user `~/.pyto/materials` root `materials.default_root()` names) so a bare
verification run and the committed evidence/run-1 are reproducible and self-contained -- this
sidesteps rather than answers `{?} MaterialsLocation`/`{?} TableScope` (is the store per-user or
shared, and should CI/demo runs default to it). Should a cross-project demo instead default to the
real per-user store (showing genuine cross-process reuse on this machine), with `--store-root`
reserved for tests and evidence generation?

`{?} ShelfDomainIsToyNotConsumer`: the "shelf" domain (a disc golf bag, invented for this task) is
a purpose-built fixture, not an existing DiscStudio consumer. Reframing 3 and the kernel-ablation
"experiment-local until two real uses" bar both lean toward real consumers earning library
promotion. Does the cross-project claim need a second REAL consumer (not a toy domain) before it is
evidence beyond "the mechanism can work," or is a deliberately small, legible toy domain the right
shape for a Day 5 proof like this one?
