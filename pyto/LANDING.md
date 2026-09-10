# Landing protocol

Landing is the only way a change becomes real. It is mechanical, it is one script, and it refuses
to proceed at the first thing that is not true. Everything else that touches git is a checkpoint
and is labelled as one.

## The caveman version

One MAIN (the clone). One EXP folder. A task is a number.

```
bash pyto/scripts/neat.sh new "what you want"   -> EXP/0, a copy of MAIN to work in (its own python)
bash pyto/scripts/neat.sh pack 0                -> the packet: intent, starting point, candidate, evidence, uncertain
bash pyto/scripts/neat.sh show 0                -> the hand-off a fresh agent explains from, after cloning
bash pyto/scripts/neat.sh land 0                -> merge into MAIN, verify there, receipt, commit, push; EXP/0 gone
bash pyto/scripts/neat.sh drop 0 <path> ...     -> "I like two of the three files": back to the start, repacked
bash pyto/scripts/neat.sh kill 0                -> abandon, nothing lands
bash pyto/scripts/neat.sh undo 0                -> a landed task back out of MAIN: revert, verify, receipt, push
bash pyto/scripts/neat.sh update 0              -> MAIN's newer commits into EXP/0 (a conflict names the files and stops)
bash pyto/scripts/neat.sh list
bash pyto/scripts/land.sh --note "one plain line"  -> onto the board under Today, committed, pushed; no receipt
python3 pyto/scripts/board_page.py > board.html    -> the board as one page for a phone (no dependencies)
```

A hand-off starts with a stopping rule (owner, 2026-09-10): read the hand-off, the board and the
packet, no more; write the one question you would answer by reading another hundred thousand
tokens, and ask the owner instead; his answer goes on the root verbatim. Reading builds a model;
asking invalidates the wrong half of it for the price of a sentence.

The board says when a task starts, not only when it lands: `neat new` writes a **started** line
with the intent, `neat kill` a **killed** line, so the owner sees what is coming before a **landed**
line appears. Both go through `land.sh --note`. A note is not a claim; only a landing is.

Every task carries a packet at `pyto/experiments/tasks/<id>/`: Intent (what you asked), Starting
point (what MAIN was), Candidate (exactly what changed), Evidence (what was checked, exit codes,
the suite table), Uncertain (the agent's `{?}` lines). The packet lives inside the experiment, so
it travels with the branch to any machine and lands with the candidate; the hand-off page tells a
fresh agent how to clone, why the repository is worth its time, and what to explain and do.
`neat land` is `land.sh --from exp/<id>` with the packet's Verify and Allow, so everything below
holds for it too. Underneath: EXP/<id> is a git worktree on branch `exp/<id>`, deleted at landing.
Control is a way back, not a gate (owner, 2026-09-09: "minimal hard stops"): `neat undo <id>`
reverts a landed task through the same protocol, so the owner never needs git to take something
back, and nothing waits on the owner to go in.

## Self-improvement, and the explicability gate

The system may improve itself: a Fable orchestrates Sonnets that mine the record (refusals, failed
receipts, the Today log, the `{?}` root, slow steps) for small useful changes to neat, landing,
the board, hand-offs, tests, scripts and docs, and tries them in parallel, one neat task each.
Branching is allowed; opacity is not. Before such a task may land it passes the explicability
gate: a cold reader who has seen nothing but the hand-off page writes, in plain words, what it
believes changed and why and which files it expects touched; a judge compares that to the real
diff. A mismatch refuses the landing, the reason goes on the packet and the board, and the task
stays packed. Bounds per branch: one plain-sentence intent, at most three files, at most 150
changed lines, no new dependency, no config. Losers are kept. Kernel semantics (what a Part, a
Calculation, a receipt means) are not in scope for the loop; they run as their own tasks.

## The words

- **Candidate**: a change that wants in, as the exact set of files it touches. It arrives as a
  branch pushed to this repository, a patch file, or edits already in the tree.
- **Package**: the brief the candidate answers. The brief names the allowed paths and the verifier
  command. If there is no brief, the package is `unbriefed` and the allowed paths are what the
  candidate touches.
- **Verifier**: a command that exits 0 or not. No judgment. It runs with the repository's own
  `.venv` first on PATH, so a bare `python3` means the same interpreter in a copy and on MAIN.
  A packet with no Verify line does not pack; `none` is the way to say there is no verifier.
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
2. **Scope.** When the package names allowed paths, every file the landing would commit must be
   under one; a file outside stops it and is named. A package without paths has no scope check.
   (Astra's packages all name paths, none of which is `pyto/src`; that is how the kernel stays
   closed to outside teams without a rule of its own.)
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

## Writers

The main tree has one writer: whoever is landing. Everyone else works in a prefixed copy of the
whole tree and hands back a branch:

```
git worktree add /home/user/wt/<package> -b wip/<package>     # the copy; agents work only there
pyto/scripts/land.sh <package> --from wip/<package> ...        # compile it back: merge, verify, receipt
```

A copy of the whole tree is the prefixed copy at the right grain: git already knows how to compile
it (merge), imports need no renaming, and two copies never race. There is no lock. A writer that
dies leaves a stale copy that blocks nobody; when its branch no longer merges, the landing refuses
with the conflicting files and nothing changes. Astra's hand-backs (`astra/<team>/<package>`) are
the same thing from outside. The landing removes the copy and its branch when it succeeds.

## Friction

A check that costs more than it catches gets disabled, so the protocol is built to be cheap on
the happy path: `land.sh <package> --from wip/<package>` is the whole command for a copy, and
`land.sh <package>` for edits made in the main tree; `--verify` and `--allow` come from the
package's brief when there is one. Every refusal names the file and the command that resolves
it. The only fixed cost is the suite, once per landing.

## Rules that do not bend

- No `git add -A` without the scope check. No commit with a failing suite. No landing while the
  tree holds anyone else's work. No disabling a check to get past it: if a check is wrong, the fix
  lands through the protocol like everything else, with the reason in the commit.
- Checkpoints are labelled `checkpoint:`; landings are labelled `land(...)`. A reader can tell
  them apart from `git log --oneline` alone.
- "Green" is a claim; it names a receipt or it is not made. (Learned the hard way on 2026-09-09:
  a checkpoint shipped with the suite red after a line-ending renormalization, and the owner was
  told "green" from a run that predated the change.)
- The receipt is the record. If the receipt says a verifier ran, its output digest is in the
  receipt, and the output is retained under `pyto/experiments/landings/<id>/`.
- Acceptance is not landing. The owner accepts or not, later, by reading; the landing receipt says
  only what was verified.
