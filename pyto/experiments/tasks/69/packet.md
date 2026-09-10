# Task 69

Intent: a test never writes into the tree it is testing: neat diff's CLI takes --diffs-dir (default pyto/experiments/review/diffs) and test_neat_diff's CLI tests pass a temp dir, so a landing's suite cannot dirty MAIN whichever pyto the child process imports (task 68 was refused for exactly that)
Starting point: 3eab7b7bfe8597b8ecc2fd82e1d1fdba45966316 (board: **refused** `task-68`: the tree was not clean (test_neat_diff's CLI test wrote into pyto/experiments/review/diffs during the suite))
Verify: cd pyto && python -m unittest tests.test_neat_diff && git status --porcelain experiments/review/diffs | grep -q . && exit 1 || true
Allow: pyto/src/pyto/neat/diff.py pyto/tests/test_neat_diff.py pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
