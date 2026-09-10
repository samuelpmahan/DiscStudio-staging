# Task 71

Intent: the owner's ten replies to the first batch, filed in his words through the loop; an answer overturns a filed default (a label answered by default keeps its number in the batch's default group until the owner speaks, and his answer supersedes it on the root and in the answer Part); the walk stops scraping quotes after the word owner: his words on a step come only from filed answers
Starting point: 4946780e26116adfbc65f85733f6796e6bc0b6ab (board: **started** `task-70`: the batch carries only what needs the owner: a ro)
Verify: cd pyto && python -m unittest tests.test_neat_review tests.test_walk && python scripts/walk.py --check && grep -c 'Owner, 2026-09-10: ' questions.md | grep -q .
Allow: pyto/src/pyto/neat/review.py pyto/tests/test_neat_review.py pyto/scripts/walk.py pyto/tests/test_walk.py pyto/experiments/review pyto/questions.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} FiledDefaultsBecomeRootEntries: filing a default under a label that had no root entry creates one (### {?} Label with a Default line), and the collator then lists it twice, as the packet item and as a root item; the second is counted as default too, so nothing is asked twice, but the batch is longer than it need be.
{?} ReviewedItemsStillAnswerable: a reviewed item (task 58 and earlier) keeps its number in the batch JSON though it is not printed, so neat answer reaches it; ChainLatencyIsTheWholeTick was answered that way.
