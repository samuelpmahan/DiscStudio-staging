# Task 3

Intent: neat anywhere: the same seven commands in any git repo, no pyto assumptions, with a selftest that proves new, pack, land and undo in a scratch repo in under two minutes
Starting point: 50ec3f7b87108ebe6d9bc5f0e448bfbbc4a8dca3 (checkpoint: neat ids count origin's exp branches; board: undo tested)
Verify: bash pyto/scripts/neat.sh selftest
Allow: pyto/scripts/neat.sh pyto/scripts/land.sh pyto/LANDING.md pyto/experiments/tasks/3
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
- {?} Plain-mode handoff: `neat pack` still writes a handoff with pyto-specific setup and `check_all.sh` commands; this approved selftest repair did not change that output.
- {?} Java verification: the selftest uses `Verify: true`; Java, Spring, Camunda, and test-automation commands must be supplied in a real task packet and were not run here.
- {?} Windows path form: MAIN's `hostpath` used `cygpath -m` (D:/...), this branch used `cygpath -w` (D:\...) for pip's target; the merge keeps one helper and the brief's `-w`, so MAIN's python install check now compares realpaths of the backslash form. Neither form could be exercised here (no cygpath on Linux); if the owner's D:/ run disagrees, flip the flag in `hostpath` alone.
- {?} `neat kill`: this branch deleted the abandoned branch locally and on origin, MAIN stopped deleting anything and prints the two commands instead. The two cannot both hold, so the merge keeps MAIN's (the later decision, task-4); the selftest does not cover kill either way.
- {?} Plain-mode receipt: the claimed/unclaimed split in land.sh still filters the literal `pyto/experiments/landings/` prefix, so in a plain repository a `.neat/landings/` file committed since base is recorded as claimed. Both sides had this; the merge left it untouched rather than widening the change.
