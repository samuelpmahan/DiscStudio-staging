# Task 143

Intent: the owner's answers of 2026-09-12 filed in his words: the export queue (a queued job is instantiated, starts as a Sequence consumed once chosen, a smart start for longer batches), the two battle receipts (in ChainSpot a Receipt IS the text and renders together), single means OnTheCourse's Single Disc as intended, and the canvas stays on the layout until he says otherwise; batch 10 collated under the fixed rule
Starting point: aa56e2932a7ec1fa0bfb4bf4309fbbc2318e04d0 (land(task-142): the demo gets a URL: the Pages workflow also deploys on a push to the sprint branch (the owner, 2026-09-12: 'PageRouter'), so the studio, its build, the browser test and the review page go live from claude/os-sprint-st8hnu without a merge to main)
Verify: cd pyto && python -m unittest tests.test_neat_review
Allow: pyto/questions.md pyto/experiments/review pyto/experiments/tasks
Candidate: 19 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/review/answers/FrameIsPartOfTheLayout.json
- A  pyto/experiments/review/answers/OneBattleTwoReceipts.json
- A  pyto/experiments/review/answers/QueueIsSessionState.json
- A  pyto/experiments/review/answers/SinglePresetIsTheProjection.json
- A  pyto/experiments/review/batches/10.json
- A  pyto/experiments/review/captures/10-240.json
- A  pyto/experiments/review/captures/10-245.json
- A  pyto/experiments/review/captures/10-247.json
- A  pyto/experiments/review/captures/10-249.json
- A  pyto/experiments/review/freezes/10-240.json
- A  pyto/experiments/review/freezes/10-245.json
- A  pyto/experiments/review/freezes/10-247.json
- A  pyto/experiments/review/freezes/10-249.json
- A  pyto/experiments/review/runs/answer-10-245.json
- A  pyto/experiments/review/runs/answer-10-247.json
- A  pyto/experiments/review/runs/answer-10-249.json
- A  pyto/experiments/review/runs/ask-10.json
- A  pyto/experiments/review/runs/default-10-240.json
- M  pyto/questions.md

```
.../review/answers/FrameIsPartOfTheLayout.json     |   11 +
 .../review/answers/OneBattleTwoReceipts.json       |   11 +
 .../review/answers/QueueIsSessionState.json        |   11 +
 .../answers/SinglePresetIsTheProjection.json       |   11 +
 pyto/experiments/review/batches/10.json            | 2251 ++++++++++++++++++++
 pyto/experiments/review/captures/10-240.json       |   11 +
 pyto/experiments/review/captures/10-245.json       |   11 +
 pyto/experiments/review/captures/10-247.json       |   11 +
 pyto/experiments/review/captures/10-249.json       |   11 +
 pyto/experiments/review/freezes/10-240.json        |    8 +
 pyto/experiments/review/freezes/10-245.json        |    8 +
 pyto/experiments/review/freezes/10-247.json        |    8 +
 pyto/experiments/review/freezes/10-249.json        |    8 +
 pyto/experiments/review/runs/answer-10-245.json    |  189 ++
 pyto/experiments/review/runs/answer-10-247.json    |  189 ++
 pyto/experiments/review/runs/answer-10-249.json    |  189 ++
 pyto/experiments/review/runs/ask-10.json           | 1703 +++++++++++++++
 pyto/experiments/review/runs/default-10-240.json   |  189 ++
 pyto/questions.md                                  |   16 +
 19 files changed, 4846 insertions(+)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_review` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.zYDwQWoFl7) (evidence/check_all.txt)
    suite                         tests  status
    library                         447  OK
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
