# Task 9

Intent: Add a fast, isolated check that land.sh's early refusal paths (bad package name, unknown branch, dirty file outside allowed paths) exit 1 and write a failed/*.json receipt without ever reaching check_all.sh, so the refusal contract is verified in under a second instead of only by hand-run scratch clones.
Starting point: 1b38f283e1e12d29a6fa73077c14c2d749c3fba8 (land(windows-venv): the scripts find the repository's .venv on their own, so isolated child processes import pyto on Windows too; the D:/ commands make that venv)
Verify: bash pyto/scripts/check_land_refusals.sh   # builds a throwaway git repo under mktemp and calls land.sh three times: (1) no args: expect exit 2 and no receipt; (2) --from a branch that does not exist: expect exit 1 and a new pyto/experiments/landings/failed/*.json; then BOARD.md is reset with git checkout because every refusal rewrites it; (3) a dirty file outside --allow: expect exit 1, a new failed receipt, the file untouched; finally asserts the working tree it started from is unchanged; no check_all.sh, no network, sub-second
Allow: pyto/scripts/check_land_refusals.sh
Candidate: 1 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/scripts/check_land_refusals.sh

```
pyto/scripts/check_land_refusals.sh | 100 ++++++++++++++++++++++++++++++++++++
 1 file changed, 100 insertions(+)
```

## Evidence

- verify: `bash pyto/scripts/check_land_refusals.sh   # builds a throwaway git repo under mktemp and calls land.sh three times: (1) no args: expect exit 2 and no receipt; (2) --from a branch that does not exist: expect exit 1 and a new pyto/experiments/landings/failed/*.json; then BOARD.md is reset with git checkout because every refusal rewrites it; (3) a dirty file outside --allow: expect exit 1, a new failed receipt, the file untouched; finally asserts the working tree it started from is unchanged; no check_all.sh, no network, sub-second` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         103  OK
    experiments/grouped-ablation    230  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           83  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

- {?} BadPackageName: the intent named "bad package name" as one of the three refusal paths, but land.sh has no format check on the package string at all -- only a missing-package check ("usage: land.sh ...", exit 2, no receipt, since it never reaches fail()). I tested that no-argument case instead and treated it as the intended meaning; if the owner meant something else by "bad", nothing here catches it.
- {?} BoardRewriteReset: every refusal calls board(), which rewrites the tracked pyto/BOARD.md in place before the receipt is written; the check resets BOARD.md with `git checkout` between refusals so the next one's scope check only sees the file that test introduces as dirty. That reset is standing in for "someone lands after a refusal, wiping its own board line" -- true in the real repo too, just not usually noticed inside one script's runtime.
- {?} Explicability: refused by the gate: The explanation's narrative says land.sh is called 'two ways' -- no-args, then a dirty file outside --allow -- but the real script (pyto/scripts/check_land_refusals.sh:66-77) makes THREE check() calls: `check no-args 2 'usage: land.sh'` (line 66), then `check unknown-branch 1 'no such branch: no-such-branch'` against `land.sh unknownbranch --from no-such-branch` (line 71), and only then `check dirty-outside-allow 1 ...` (line 77). The unknown-branch refusal path -- explicitly named in the packet's own Intent line (pyto/experiments/tasks/9/packet.md:3, 'bad package name, unknown branch, dirty file outside allowed paths') -- is entirely missing from the explanation's step-by-step account.; Because the explanation collapses three calls into two, it also misplaces the BOARD.md reset: it says reset_board runs 'between the two calls' (i.e. between no-args and dirty-file), but the real code (check_land_refusals.sh:73, `reset_board` immediately after the unknown-branch check and before the dirty-outside-allow check) resets BOARD.md between the unknown-branch check and the dirty-file check, not between no-args and dirty-file.; The confusions list hedges that 'it is unclear ... whether the unknown branch refusal path ... is actually covered ... or left untested', but the explanation's main body still asserts a definite two-call story rather than flagging the omission as a real gap -- so the flagged uncertainty didn't prevent a wrong factual claim from being presented as fact.. The hand-off should have said: The hand-off page's Verify description (pyto/experiments/tasks/9/packet.md's Verify line) should have named all three land.sh invocations the script actually runs -- no-args (exit 2, no receipt), an unknown --from branch (exit 1, new failed receipt), and a dirty file outside --allow (exit 1, new failed receipt) -- and noted that the BOARD.md `git checkout` reset sits between the second and third calls, so the cold reader wasn't left to infer (and undercount) the test structure from a bare diffstat.
