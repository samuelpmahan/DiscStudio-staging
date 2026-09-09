# Task 5

Intent: Add a standalone, sub-second selftest that every committed landing receipt JSON (verified and failed) has the fields land.sh actually writes, so a schema regression in land.sh is caught without running check_all.sh or a scratch clone.
Starting point: 1b38f283e1e12d29a6fa73077c14c2d749c3fba8 (land(windows-venv): the scripts find the repository's .venv on their own, so isolated child processes import pyto on Windows too; the D:/ commands make that venv)
Verify: bash pyto/scripts/check_receipts.sh   # exits 0 iff every receipt.json under pyto/experiments/landings/**/*.json has the required keys for its result type and 'result' is 'verified' or 'failed'; runs in well under a second, no venv, no git network call
Allow: pyto/scripts/check_receipts.sh
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

- {?} Key presence only: check_receipts.sh checks that each required key exists, not its type or
  shape (e.g. `check_all.counts` could silently become a list instead of an object, `claimed`
  could become a string, and the check would still pass). Matched the caveman-simple / no-friction
  instruction; a stricter shape check is easy to add later if the owner wants it.
- {?} Where receipts live: it walks every `*.json` under `pyto/experiments/landings/`, trusting
  LANDING.md's word that the whole directory is receipts (one JSON per landing attempt, verified
  ones under an id folder, failed ones under `failed/`). If some other JSON ever lands there for
  an unrelated reason, this would flag it as a bad receipt.
