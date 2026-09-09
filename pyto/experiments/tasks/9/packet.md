# Task 9

Intent: Add a fast, isolated check that land.sh's early refusal paths (bad package name, unknown branch, dirty file outside allowed paths) exit 1 and write a failed/*.json receipt without ever reaching check_all.sh, so the refusal contract is verified in under a second instead of only by hand-run scratch clones.
Starting point: 1b38f283e1e12d29a6fa73077c14c2d749c3fba8 (land(windows-venv): the scripts find the repository's .venv on their own, so isolated child processes import pyto on Windows too; the D:/ commands make that venv)
Verify: bash pyto/scripts/check_land_refusals.sh   # builds a throwaway git repo under mktemp, calls land.sh with no args (expect exit 2), then with a dirty file outside --allow (expect exit 1 and a new pyto/experiments/landings/failed/*.json), asserts the working tree it started from is untouched; no check_all.sh, no network, sub-second
Allow: pyto/scripts/check_land_refusals.sh
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

- {?} BadPackageName: the intent named "bad package name" as one of the three refusal paths, but land.sh has no format check on the package string at all -- only a missing-package check ("usage: land.sh ...", exit 2, no receipt, since it never reaches fail()). I tested that no-argument case instead and treated it as the intended meaning; if the owner meant something else by "bad", nothing here catches it.
- {?} BoardRewriteReset: every refusal calls board(), which rewrites the tracked pyto/BOARD.md in place before the receipt is written; the check resets BOARD.md with `git checkout` between refusals so the next one's scope check only sees the file that test introduces as dirty. That reset is standing in for "someone lands after a refusal, wiping its own board line" -- true in the real repo too, just not usually noticed inside one script's runtime.
