# Task 150

Intent: the owner, 2026-09-12: 'come up with some compiler-ish efficiency pass to prevent things like this? Encode a path to trusting the sparsification of things' -- neat hot names the hot Calculations and the shape of their values over one run record (a dense list that would be an array, cost per element, an over-cap value, a cache that isn't there), and neat equiv rebuilds every receipt's inputs, runs a candidate and witnesses that it reproduces every recorded result
Starting point: 7c354c04e7da2a5323fdb3a92e4ccf8223068cfe (board: **started** `task-149`: materializing a record with big values is cheap:)
Verify: bash pyto/scripts/check_all.sh
Allow: pyto/src/pyto/neat/hot.py pyto/src/pyto/neat/equiv.py pyto/scripts/neat.sh pyto/USE.md pyto/tests/test_neat_hot.py pyto/tests/test_neat_equiv.py pyto/tests/test_use.py pyto/experiments/review/hot pyto/experiments/review/equiv pyto/BOARD.md pyto/questions.md
Candidate: 7 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/USE.md
- M  pyto/scripts/neat.sh
- A  pyto/src/pyto/neat/equiv.py
- A  pyto/src/pyto/neat/hot.py
- A  pyto/tests/test_neat_equiv.py
- A  pyto/tests/test_neat_hot.py
- M  pyto/tests/test_use.py

```
pyto/USE.md                   | 125 ++++++++++++
 pyto/scripts/neat.sh          |  26 ++-
 pyto/src/pyto/neat/equiv.py   | 430 ++++++++++++++++++++++++++++++++++++++++
 pyto/src/pyto/neat/hot.py     | 452 ++++++++++++++++++++++++++++++++++++++++++
 pyto/tests/test_neat_equiv.py | 277 ++++++++++++++++++++++++++
 pyto/tests/test_neat_hot.py   | 201 +++++++++++++++++++
 pyto/tests/test_use.py        |   1 +
 7 files changed, 1511 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `bash pyto/scripts/check_all.sh` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.ra0ZONnHXi) (evidence/check_all.txt)
    suite                         tests  status
    library                         544  OK
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

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} HotPerElementThreshold: neat hot calls an invocation per-element when it spends more than 50 ns on each element, over at least 1024 of them. Calibrated on the generation: dense, every stage trips it (render 1358 ns per pixel, fitness 345, encode 86); over arrays nothing does. The default stands until the owner says otherwise; it is one number at the top of hot.py and --per-element overrides it per run.

{?} EquivShapeNotInTheDigest: neat equiv canonicalizes a (256, 256, 3) uint8 array and the flat list of 196,608 ints to the same bytes -- the shape is deliberately not in the digest, because the owner's own trust was the 32 pixel hashes and a list of pixels is the same pixels as an array of them. The default is that a reshape is not a difference; if a candidate should have to reproduce the shape too, that is one line in canonical.
