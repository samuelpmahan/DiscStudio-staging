# Task 3 brief: neat anywhere

For two implementers (Lunas) on disjoint files, one Terra that integrates and runs the selftest,
and Astra who assigns and reads the hand-back and implements nothing. Written to be cheap: each
Luna reads only the files named in its lane, runs only the commands named there, and stops when
its own check passes; the Terra runs the selftest and does at most two repair rounds. Expected
effort: an hour or two of careful editing in parallel, a few minutes of machine time.

## What neat is, in five lines

`pyto/scripts/neat.sh` is version control for people who do not want to think about git: one MAIN
(the clone), one EXP folder of numbered copies, and a task is a number. `neat new "intent"` makes
EXP/<id>; an agent works there; `neat pack <id>` writes the packet (intent, starting point,
candidate, evidence, uncertain) and a hand-off page; `neat land <id>` merges into MAIN, runs the
verifier, writes a receipt, commits `land(task-<id>): ...`, pushes, and writes one line under
"## Today" on the board; `neat undo <id>` takes it back out the same way. `pyto/scripts/land.sh`
is the landing itself. Read `pyto/LANDING.md` first (the top section is enough), then the two
scripts in full. They are 480 lines together.

## The problem

Both scripts assume they live in this repository: the landing receipts go under
`pyto/experiments/landings/`, the packets under `pyto/experiments/tasks/`, the board is
`pyto/BOARD.md`, `neat new` builds a Python venv and pip-installs `pyto`, and `land.sh` runs
`pyto/scripts/check_all.sh` as the suite. The owner wants the same seven commands on a work laptop
where none of that exists, for any repository, with only Git Bash and python available (and no
Claude Code or Codex there, only editor agents that can run a shell command).

## What to build

1. **No pyto assumptions.** When the repo has no `pyto/pyproject.toml`, skip the venv and the
   pip install. When there is no `pyto/scripts/check_all.sh`, the suite is the packet's `Verify:`
   command alone (and when that is `none`, landing verifies nothing and says so in the receipt).
   Receipts, packets and the board move to a repo-relative `.neat/` when `pyto/` is absent:
   `.neat/landings/`, `.neat/tasks/<id>/`, `.neat/BOARD.md` (with a `## Today` section created on
   first use). When `pyto/` is present, everything stays exactly where it is today, byte for byte
   in behaviour, so this repository's own landings do not change.
2. **Two files, copied anywhere.** `neat.sh` and `land.sh` must work when copied side by side into
   any directory inside a git repository (they already resolve their own location; keep that, and
   resolve MAIN with `git rev-parse --show-toplevel` from that location rather than assuming
   `../..`).
3. **`neat selftest`.** A new subcommand: makes a temporary directory with a bare origin and a
   clone of a tiny repository (one file, a `Verify:` that is `true`), copies the two scripts into
   it, then runs new, an edit, pack, land, and undo, and checks after each step exactly what the
   hand-off promises: the copy exists, the packet has the four sections, the landing commit is
   labelled `land(task-0)`, the branch is gone from the bare origin, the board has the line, and
   after undo the edit is gone and the tree is clean. Exit 0 only when every check holds; print
   one line per check. It must finish in under two minutes on a laptop and must not touch the
   repository it was run from.
4. **Git Bash on Windows.** Do not break what task 1 fixed (`exp/1` on origin: pip gets a host
   path via `cygpath -w` when present, the install check asks python rather than a shell glob).
   Use `command -v python3 || command -v python`, never a bare `python3`.

## The split, so nobody has to talk

The two scripts share one layout rule and one command-line contract. Both are fixed here; each
Luna implements its side and never edits the other's file.

**Layout rule (both files, same logic, each its own copy):** `ROOT="$(git rev-parse --show-toplevel)"`
from the script's own directory. If `$ROOT/pyto/pyproject.toml` exists: pyto mode, and every
path stays exactly what it is today (`pyto/experiments/landings`, `pyto/experiments/tasks`,
`pyto/BOARD.md`, suite `pyto/scripts/check_all.sh`, the venv and pip install in `neat new`).
Otherwise: plain mode, `.neat/landings`, `.neat/tasks/<id>`, `.neat/BOARD.md` (created with a
title and a `## Today` section on first use), no venv, no pip, and the suite is the packet's
`Verify:` alone (`none` means the landing verifies nothing and the receipt says so). `.neat/` is
committed, not ignored: it is the record.

**Command-line contract (unchanged):** `land.sh <package> [--from <branch>] [--verify "<cmd>"]
[--allow "<paths>"] [--base <sha>] [--message "<line>"] [--dry-run]`, exit 0 only on a landing.
`neat.sh` calls it exactly as today.

**Luna A owns `pyto/scripts/land.sh`:** the layout rule; `LAND_DIR`, the receipt and board paths
from it; the suite step runs `check_all.sh` only in pyto mode; the board function creates
`.neat/BOARD.md` when absent; `$PYTHON` resolved as `command -v python3 || command -v python`.
Check: `bash -n land.sh`, then in a scratch git repo with one committed file and no `pyto/`, a
dirty edit lands with `--verify true` and writes `.neat/landings/<id>/receipt.json` and a
`## Today` line in `.neat/BOARD.md`; and in this repository `--dry-run` still names
`pyto/experiments/landings`.

**Luna B owns `pyto/scripts/neat.sh`:** the layout rule; `TASKS` and `EXP` from it; `neat new`
skips the venv and pip in plain mode (keep task 1's Windows fixes: `cygpath -w` for pip, the
install check asks python); `next_id`, `pack`, `show`, `drop`, `land`, `kill`, `undo`, `list` use
the resolved paths; and the new `selftest` subcommand described above, which copies both scripts
into the scratch repo it builds. Check: `bash -n neat.sh`, then `neat selftest` against the
current `land.sh` (it may fail on Luna A's half until the Terra integrates; that is expected).

**Terra:** merge nothing by hand; both Lunas commit to `exp/3`, disjoint files, so git does it.
Run `bash pyto/scripts/neat.sh selftest`; on failure, read the failing check's line, fix the one
file it names (or send the line back to that Luna), at most two rounds. Then hand back. Never run
`pyto/scripts/check_all.sh`; the cloud session runs it once at pack.

## Verify

```
bash pyto/scripts/neat.sh selftest        # exit 0, one line per check
bash -n pyto/scripts/neat.sh && bash -n pyto/scripts/land.sh
```

Do not run `pyto/scripts/check_all.sh` yourself; the cloud session runs it once when it packs and
lands this task.

## Hand back

Commit on this branch (`exp/3`) with messages starting `exp/3:` (Lunas: `exp/3: land.sh ...` and
`exp/3: neat.sh ...`; Terra: `exp/3: selftest green`), push it, and stop. Append one
`- {?} Label: description` line under "## Uncertain" in `pyto/experiments/tasks/3/packet.md` for
anything you were unsure about (for example: should `.neat/` be committed or ignored in a foreign
repo; default: committed, it is the record). Touch nothing outside the files named in the packet's
`Allow:` line.
