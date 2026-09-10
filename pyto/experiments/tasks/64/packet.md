# Task 64

Intent: the owner's words on what this is for and how the frontier runs through him: pyto/questions.md gains SuperGoogle (verbatim: a Python lib anyone can use to figure stuff out so long as they do something real and meaningful; AI as super Google and Python creator powers he can conceive but not implement; not distilling anything; the projection of his reasoning is a molecule) and TinyQuestions (the frontier workflow is tailored for subagent throughput through him: as many little questions as possible, answered by him, filed in his words; defaults are for nothing that carries meaning); FRONTIER.md's opening paragraph says so
Starting point: 2810f4efa75371153d5c2ba6e4517750c8346780 (land(task-63): the walk: the owner, 2026-09-10: 'make it real easy for me and Astra to step through your landings, inspect changes, keep all PQL, PxC, etc front of mind automatically'. pyto/scripts/walk.py builds walk.html from the record alone: one step per landing in order (intent, the owner's words it quotes, the receipt, files changed with counts and the diff folded, the packet's {?} lines, which of the seven concepts it touched with their one-line definitions pinned at the top of every step, and the sentence that undoes it); arrow keys step; --text N prints one step for an agent and neat walk N dispatches to it; same tree, same bytes; a test pins that every landing on the board has a step)
Verify: grep -q 'SuperGoogle' pyto/questions.md && grep -q 'TinyQuestions' pyto/questions.md && grep -q 'through the owner' pyto/FRONTIER.md
Allow: pyto/questions.md pyto/FRONTIER.md pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/FRONTIER.md
- M  pyto/questions.md

```
pyto/FRONTIER.md  |  2 +-
 pyto/questions.md | 28 ++++++++++++++++++++++++++++
 2 files changed, 29 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `grep -q 'SuperGoogle' pyto/questions.md && grep -q 'TinyQuestions' pyto/questions.md && grep -q 'through the owner' pyto/FRONTIER.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.61HpmQHtmz) (evidence/check_all.txt)
    suite                         tests  status
    library                         336  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules             5  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
