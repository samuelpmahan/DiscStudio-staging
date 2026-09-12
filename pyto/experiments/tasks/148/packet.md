# Task 148

Intent: sam-mode: the owner's working conventions, mined from his own words across the session and the board, as a Claude Code skill (.claude/skills/sam-mode) with a three-line CLAUDE.md pointing at it, so every fresh agent in this repository works his way without being told
Starting point: 510b5aed3836aa83c8c4423fd752844b13d971d4 (board: **started** `task-147`: pyto study on a table that is not tiny: a seeded)
Verify: test -s .claude/skills/sam-mode/SKILL.md && head -1 .claude/skills/sam-mode/SKILL.md | grep -q '^---$' && grep -q '^name: sam-mode$' .claude/skills/sam-mode/SKILL.md && grep -q sam-mode CLAUDE.md
Allow: .claude/skills/sam-mode/SKILL.md CLAUDE.md pyto/BOARD.md pyto/questions.md
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  .claude/skills/sam-mode/SKILL.md
- A  CLAUDE.md

```
.claude/skills/sam-mode/SKILL.md | 113 +++++++++++++++++++++++++++++++++++++++
 CLAUDE.md                        |   3 ++
 2 files changed, 116 insertions(+)
```

## Evidence

- verify: `test -s .claude/skills/sam-mode/SKILL.md && head -1 .claude/skills/sam-mode/SKILL.md | grep -q '^---$' && grep -q '^name: sam-mode$' .claude/skills/sam-mode/SKILL.md && grep -q sam-mode CLAUDE.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.tntUNiPkcv) (evidence/check_all.txt)
    suite                         tests  status
    library                         472  OK
    experiments/brain               756  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
