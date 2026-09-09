# Task 3 brief: neat anywhere

For one Codex agent, working alone. Written to be cheap: read only the files named here, run only
the commands named here, stop when the selftest passes. Expected effort: one to two hours of
careful editing, a few minutes of machine time.

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

## Verify

```
bash pyto/scripts/neat.sh selftest        # exit 0, one line per check
bash -n pyto/scripts/neat.sh && bash -n pyto/scripts/land.sh
```

Do not run `pyto/scripts/check_all.sh` yourself; the cloud session runs it once when it packs and
lands this task.

## Hand back

Commit on this branch (`exp/3`) with messages starting `exp/3:`, push it, and stop. Append one
`- {?} Label: description` line under "## Uncertain" in `pyto/experiments/tasks/3/packet.md` for
anything you were unsure about (for example: should `.neat/` be committed or ignored in a foreign
repo; default: committed, it is the record). Touch nothing outside the files named in the packet's
`Allow:` line.
