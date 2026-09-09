# Task 12

Intent: proof: the test as one script. proof.sh clones the branch fresh into a temp dir on this drive, runs the board's commands verbatim, writes one Today line with the result and a receipt under pyto/experiments/landings/proofs/
Starting point: 76bc3d2a51c0e5442a0e4e8f519fe7d01484e9f5 (land(task-11): Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test)
Verify: bash pyto/scripts/proof.sh --selftest
Allow: pyto/scripts/proof.sh pyto/experiments/proofs
Candidate: 1 files, see below
Evidence: suite exit 1, see below

## Candidate

- A  pyto/scripts/proof.sh

```
pyto/scripts/proof.sh | 149 ++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 149 insertions(+)
```

## Evidence

- verify: `bash pyto/scripts/proof.sh --selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 1, last line: SOME SUITES FAILED (logs in /tmp/tmp.UuDWjgdu5g) (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/grouped-ablation    240  FAIL
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           87  OK
    viewer-record-schema             19  OK
    
    SOME SUITES FAILED (logs in /tmp/tmp.UuDWjgdu5g)

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} Receipt result vocabulary: proof.sh writes `"result": "green"/"red"` per the brief, but
`check_receipts.sh` walks all of `pyto/experiments/landings/` (proofs/ included) and only accepts
`"result": "verified"/"failed"` with land.sh's key set. A committed proof receipt will read as
malformed if that script is ever run over the whole tree. Default taken: keep `green`/`red` as
specified (a proof is not a landing and carries its own schema, `pyto-proof-receipt@1`) and leave
`check_receipts.sh` untouched, since widening it is outside this task's three-file, 150-line bound.
{?} `cd` tracking is best-effort: proof.sh only recognizes a bare `cd <path>` line (optionally with
a trailing `#` comment) to update the working directory carried into the next step; a `cd` folded
into a compound command (e.g. `cd x && y`) would not update the tracked cwd for later steps. The
board's current block only uses a standalone `cd` line, so this does not bite today. Default taken:
leave it, since the board's test is the only input this script parses.
{?} Step granularity: each *line* of the fenced block is treated as one step, so
`python -m venv .venv && .venv/Scripts/python -m pip install ...` is one step even though it does
two things; if the venv step fails, pip install never runs (`&&` short-circuits) and that whole
line is reported as one failing step. Default taken: line-granularity, since the board's block is
already written one logical action per line and the brief calls the block's own lines "commands."
