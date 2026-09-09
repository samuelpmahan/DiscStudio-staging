# Task 3 for a Codex agent: neat anywhere

Branch `exp/3` on `samuelpmahan/DiscStudio-staging`. The brief is on the branch at
`pyto/experiments/tasks/3/BRIEF.md`; the packet (intent, starting point, verify, allow) is
`packet.md` beside it. Shape: two Lunas on disjoint files (A: `land.sh`, B: `neat.sh` plus the `selftest`
subcommand), one Terra that runs the selftest and does at most two repair rounds, Astra assigns
and reads the hand-back and implements nothing. The brief fixes the layout rule and the
command-line contract so the Lunas never need to talk. Each reads only the files its lane names,
runs only the commands named there, and stops when its check passes. Hand back by
committing on `exp/3` with messages starting `exp/3:` and pushing. The cloud session packs and
lands it and writes the line on the board.

Paste this to Astra:

```
Task 3, "neat anywhere": clone https://github.com/samuelpmahan/DiscStudio-staging.git, branch
exp/3, brief at pyto/experiments/tasks/3/BRIEF.md. Assign one Terra. The Terra gives Luna A the
land.sh lane and Luna B the neat.sh lane exactly as the brief's "The split" section states, in
parallel, each editing only its own file and running only its own check. When both have pushed to
exp/3, the Terra runs `bash pyto/scripts/neat.sh selftest`, repairs at most twice, commits
"exp/3: selftest green", pushes, and reports. You implement nothing; you read the report and
forward any "{?}" lines from pyto/experiments/tasks/3/packet.md. Nobody runs check_all.sh.
```

If you run it with a single agent instead, the same brief works: do lane A, then lane B, then the
Terra's step.
