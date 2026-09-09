# Task 15

Intent: proof.sh gives each run its own output dir: the board's pyto-hit path is substituted like the clone path, so a second proof on one machine cannot trip over the first
Starting point: 3b6c3ae047eaea552c2cd109ce5931c061b8cf34 (proof: fresh clone on D:/ after tasks 12, 13, 14 (receipt under pyto/experiments/proofs))
Verify: bash pyto/scripts/proof.sh --selftest
Allow: pyto/scripts/proof.sh
Candidate: 1 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/scripts/proof.sh

```
pyto/scripts/proof.sh | 10 +++++++++-
 1 file changed, 9 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `bash pyto/scripts/proof.sh --selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/grouped-ablation    240  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           87  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
