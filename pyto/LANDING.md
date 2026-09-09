# Landing protocol

Landing is the only way a change becomes real. It is mechanical, it is one script, and it refuses
to proceed at the first thing that is not true. Everything else that touches git is a checkpoint
and is labelled as one.

## The words

- **Candidate**: a change that wants in, as the exact set of files it touches. It arrives as a
  branch pushed to this repository, a patch file, or edits already in the tree.
- **Package**: the brief the candidate answers. The brief names the allowed paths and the verifier
  command. If there is no brief, the package is `unbriefed` and the allowed paths are what the
  candidate touches.
- **Verifier**: a command that exits 0 or not. No judgment.
- **Landing receipt**: one JSON file per landing attempt, under `pyto/experiments/landings/`,
  committed with the landing. A failed attempt gets a receipt too, under `failed/`.
- **Landed**: on the working branch, every suite green, the receipt committed, pushed.
- **Checkpoint**: any other commit. Labelled `checkpoint:`. Never a claim.

## The protocol

```
pyto/scripts/land.sh <package> [--verify "<command>"] [--allow "<path> <path> ..."] [--base <sha>] [--dry-run]
```

`--base` is the commit the package started from. This session's stop hook commits the tree at the
end of every turn, so checkpoints are unavoidable; they never claim anything. A landing claims:
its receipt lists every file changed since base, split into **claimed** (under the allowed paths,
this package's) and **unclaimed** (present, verified with the mixture, someone else's, still
awaiting their own landing). Over time the unclaimed lists shrink to nothing.

1. **Clean start.** `git status` must show nothing but the candidate. If another candidate's files
   are in the tree, stop: one writer per directory at a time, and one landing at a time. The
   script never moves anyone's files; it names them and prints the parking command
   (`git stash push -u -m parked -- <paths>`, land, `git stash pop`) for when their writer is done.
2. **Scope.** Every changed file must be under an allowed path. A file outside stops the landing.
   `pyto/src` is never allowed unless the package says so by name.
3. **Verify.** Run the package's verifier, then `bash pyto/scripts/check_all.sh`. Both must exit 0.
   Outputs are captured, not summarized.
4. **Record.** Write the receipt: package, base sha, claimed and unclaimed files with sizes and digests, verifier commands
   with exit codes and sha256 of their outputs, suite counts, the `{?}` entries the candidate
   brought (merged into `pyto/questions.md` in the same commit), who landed it, when.
5. **Commit and push.** Only the files that were dirty at step 1, plus the receipt; if the tree
   moved while the suites ran, stop. Message `land(<package>): <one line>`, body naming the
   receipt. Push. The result sha goes back into the receipt on the next landing (a receipt cannot
   contain its own commit).
6. **Close.** Update the lane's "Stands" line on `pyto/BOARD.md` and regenerate the status page.
   Delete the delivery branch if there was one.

On any failure at steps 1 to 3: nothing is committed except a failed receipt under
`pyto/experiments/landings/failed/` with the reason, the tree is left as it was for inspection,
and the findings go back to whoever sent the candidate.

## Rules that do not bend

- No `git add -A` without the scope check. No commit with a failing suite. No landing while the
  tree holds anyone else's work.
- Checkpoints are labelled `checkpoint:`; landings are labelled `land(...)`. A reader can tell
  them apart from `git log --oneline` alone.
- The receipt is the record. If the receipt says a verifier ran, its output digest is in the
  receipt, and the output is retained under `pyto/experiments/landings/<id>/`.
- Acceptance is not landing. The owner accepts or not, later, by reading; the landing receipt says
  only what was verified.
