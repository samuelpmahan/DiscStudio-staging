# Task 4

Intent: Stop `neat kill` from deleting the abandoned task's branch (local and on origin); only remove the disposable worktree directory.
Starting point: 1b38f283e1e12d29a6fa73077c14c2d749c3fba8 (land(windows-venv): the scripts find the repository's .venv on their own, so isolated child processes import pyto on Windows too; the D:/ commands make that venv)
Verify: id=$(bash pyto/scripts/neat.sh new "throwaway" | sed -n 's/^Task \([0-9]*\).*/\1/p'); bash pyto/scripts/neat.sh kill "$id"; git rev-parse --verify "exp/$id" >/dev/null && [ ! -d "EXP/$id" ] && ! bash pyto/scripts/neat.sh list | awk '{print $1}' | grep -qx "$id"
Allow: pyto/scripts/neat.sh
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
- {?} Verify field rewritten: the Verify string given at task creation was prose ("note <id> ...
  then `git rev-parse ...` should still resolve"), not executable bash, and its backticks would
  have been expanded by the shell that invoked `neat new` itself. I rewrote it to a literal
  one-line script with the same intent (make a throwaway task, kill it, check the branch survives,
  the worktree dir is gone, and it drops off `neat list`) so `neat pack` actually runs it instead
  of recording a spurious non-zero exit. Manually re-derived and re-ran before packing; owner may
  want to confirm the translation kept the intent.
- {?} Origin branch left forever: `neat kill` now leaves `exp/<id>` on origin too, unbounded, for
  every killed task from now on. That matches "nothing is deleted" and "Losers are kept" (`pyto/BOARD.md:202-203`)
  but there is no companion command to reap old killed branches later if the owner ever wants one;
  out of scope for this change (bounds: one file, one intent).
