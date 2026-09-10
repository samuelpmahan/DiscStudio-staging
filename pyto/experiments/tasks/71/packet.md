# Task 71

Intent: the owner's ten replies to the first batch, filed in his words through the loop; an answer overturns a filed default (a label answered by default keeps its number in the batch's default group until the owner speaks, and his answer supersedes it on the root and in the answer Part); the walk stops scraping quotes after the word owner: his words on a step come only from filed answers
Starting point: 4946780e26116adfbc65f85733f6796e6bc0b6ab (board: **started** `task-70`: the batch carries only what needs the owner: a ro)
Verify: cd pyto && python -m unittest tests.test_neat_review tests.test_walk && python scripts/walk.py --check && grep -c 'Owner, 2026-09-10: ' questions.md | grep -q .
Allow: pyto/src/pyto/neat/review.py pyto/tests/test_neat_review.py pyto/scripts/walk.py pyto/tests/test_walk.py pyto/experiments/review pyto/questions.md pyto/experiments/tasks
Candidate: 46 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/review/answers/BatchItemTextLength.json
- A  pyto/experiments/review/answers/ChainLatencyIsTheWholeTick.json
- M  pyto/experiments/review/answers/FileIsNotAnEffect.json
- M  pyto/experiments/review/answers/MoleculeAddress.json
- A  pyto/experiments/review/answers/MoleculeScheme.json
- A  pyto/experiments/review/answers/NeatIsAMount.json
- A  pyto/experiments/review/answers/OwnerQuotes.json
- A  pyto/experiments/review/answers/RefusedAndKilledSteps.json
- A  pyto/experiments/review/answers/RootLabelsCountAsOpen.json
- A  pyto/experiments/review/answers/StubOpensTheSelftest.json
- A  pyto/experiments/review/batches/8.json
- A  pyto/experiments/review/captures/7-1.json
- A  pyto/experiments/review/captures/7-2.json
- A  pyto/experiments/review/captures/7-3.json
- A  pyto/experiments/review/captures/7-4.json
- A  pyto/experiments/review/captures/7-5.json
- A  pyto/experiments/review/captures/7-6.json
- A  pyto/experiments/review/captures/7-7.json
- A  pyto/experiments/review/captures/8-157.json
- A  pyto/experiments/review/captures/8-215.json
- A  pyto/experiments/review/captures/8-225.json
- A  pyto/experiments/review/freezes/7-1.json
- A  pyto/experiments/review/freezes/7-2.json
- A  pyto/experiments/review/freezes/7-3.json
- A  pyto/experiments/review/freezes/7-4.json
- A  pyto/experiments/review/freezes/7-5.json
- A  pyto/experiments/review/freezes/7-6.json
- A  pyto/experiments/review/freezes/7-7.json
- A  pyto/experiments/review/freezes/8-157.json
- A  pyto/experiments/review/freezes/8-215.json
- A  pyto/experiments/review/freezes/8-225.json
- A  pyto/experiments/review/runs/answer-7-1.json
- A  pyto/experiments/review/runs/answer-7-2.json
- A  pyto/experiments/review/runs/answer-7-3.json
- A  pyto/experiments/review/runs/answer-7-4.json
- A  pyto/experiments/review/runs/answer-7-5.json
- A  pyto/experiments/review/runs/answer-7-6.json
- A  pyto/experiments/review/runs/answer-7-7.json
- A  pyto/experiments/review/runs/answer-8-157.json
- A  pyto/experiments/review/runs/answer-8-215.json
- A  pyto/experiments/review/runs/answer-8-225.json
- A  pyto/experiments/review/runs/ask-8.json
- M  pyto/questions.md
- M  pyto/scripts/walk.py
- M  pyto/src/pyto/neat/review.py
- M  pyto/tests/test_neat_review.py

```
.../review/answers/BatchItemTextLength.json        |   11 +
 .../review/answers/ChainLatencyIsTheWholeTick.json |   11 +
 .../review/answers/FileIsNotAnEffect.json          |   10 +-
 .../review/answers/MoleculeAddress.json            |   10 +-
 .../experiments/review/answers/MoleculeScheme.json |   11 +
 pyto/experiments/review/answers/NeatIsAMount.json  |   11 +
 pyto/experiments/review/answers/OwnerQuotes.json   |   11 +
 .../review/answers/RefusedAndKilledSteps.json      |   11 +
 .../review/answers/RootLabelsCountAsOpen.json      |   11 +
 .../review/answers/StubOpensTheSelftest.json       |   11 +
 pyto/experiments/review/batches/8.json             | 2147 ++++++++++++++++++++
 pyto/experiments/review/captures/7-1.json          |   11 +
 pyto/experiments/review/captures/7-2.json          |   11 +
 pyto/experiments/review/captures/7-3.json          |   11 +
 pyto/experiments/review/captures/7-4.json          |   11 +
 pyto/experiments/review/captures/7-5.json          |   11 +
 pyto/experiments/review/captures/7-6.json          |   11 +
 pyto/experiments/review/captures/7-7.json          |   11 +
 pyto/experiments/review/captures/8-157.json        |   11 +
 pyto/experiments/review/captures/8-215.json        |   11 +
 pyto/experiments/review/captures/8-225.json        |   11 +
 pyto/experiments/review/freezes/7-1.json           |    8 +
 pyto/experiments/review/freezes/7-2.json           |    8 +
 pyto/experiments/review/freezes/7-3.json           |    8 +
 pyto/experiments/review/freezes/7-4.json           |    8 +
 pyto/experiments/review/freezes/7-5.json           |    8 +
 pyto/experiments/review/freezes/7-6.json           |    8 +
 pyto/experiments/review/freezes/7-7.json           |    8 +
 pyto/experiments/review/freezes/8-157.json         |    8 +
 pyto/experiments/review/freezes/8-215.json         |    8 +
 pyto/experiments/review/freezes/8-225.json         |    8 +
 pyto/experiments/review/runs/answer-7-1.json       |  189 ++
 pyto/experiments/review/runs/answer-7-2.json       |  189 ++
 pyto/experiments/review/runs/answer-7-3.json       |  189 ++
 pyto/experiments/review/runs/answer-7-4.json       |  189 ++
 pyto/experiments/review/runs/answer-7-5.json       |  189 ++
 pyto/experiments/review/runs/answer-7-6.json       |  189 ++
 pyto/experiments/review/runs/answer-7-7.json       |  189 ++
 pyto/experiments/review/runs/answer-8-157.json     |  189 ++
 pyto/experiments/review/runs/answer-8-215.json     |  189 ++
 pyto/experiments/review/runs/answer-8-225.json     |  189 ++
 pyto/experiments/review/runs/ask-8.json            | 1671 +++++++++++++++
 pyto/questions.md                                  |   36 +
 pyto/scripts/walk.py                               |   20 +-
 pyto/src/pyto/neat/review.py                       |   41 +-
 pyto/tests/test_neat_review.py                     |   13 +-
 46 files changed, 6089 insertions(+), 27 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_review tests.test_walk && python scripts/walk.py --check && grep -c 'Owner, 2026-09-10: ' questions.md | grep -q .` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.nUFGj25dY6) (evidence/check_all.txt)
    suite                         tests  status
    library                         368  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} FiledDefaultsBecomeRootEntries: filing a default under a label that had no root entry creates one (### {?} Label with a Default line), and the collator then lists it twice, as the packet item and as a root item; the second is counted as default too, so nothing is asked twice, but the batch is longer than it need be.
{?} ReviewedItemsStillAnswerable: a reviewed item (task 58 and earlier) keeps its number in the batch JSON though it is not printed, so neat answer reaches it; ChainLatencyIsTheWholeTick was answered that way.
