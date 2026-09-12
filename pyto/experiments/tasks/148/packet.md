# Task 148

Intent: sam-mode: the owner's working conventions, mined from his own words across the session and the board, as a Claude Code skill (.claude/skills/sam-mode) with a three-line CLAUDE.md pointing at it, so every fresh agent in this repository works his way without being told
Starting point: 510b5aed3836aa83c8c4423fd752844b13d971d4 (board: **started** `task-147`: pyto study on a table that is not tiny: a seeded)
Verify: test -s .claude/skills/sam-mode/SKILL.md && head -1 .claude/skills/sam-mode/SKILL.md | grep -q '^---$' && grep -q '^name: sam-mode$' .claude/skills/sam-mode/SKILL.md && grep -q sam-mode CLAUDE.md
Allow: .claude/skills/sam-mode/SKILL.md CLAUDE.md pyto/BOARD.md pyto/questions.md
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
