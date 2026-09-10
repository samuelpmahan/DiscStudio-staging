# Task 77

Intent: USE.md section 4 still teaches the rule the owner overturned: 'the Calculations of one Tick are parallel branches, so none of them may read another's produce'; it now says what the kernel does since task 57 (inside a Tick the Calculations are a sequence in declared order, a later one may bind an earlier sibling's result, a Tick with no sibling reads may run at once, a read of a later sibling and two siblings on one address are refused) with a chained Tick in the block and its printed output, and every other page that repeats the old sentence is corrected
Starting point: 56f1bf6acc6f129d8dd3183f0ce44d81bc60a3e7 (land(task-76): a landing finishes on its own when a candidate deletes a file and starts ignoring it: land.sh step 5 staged each dirty path with git add -A, which is fatal for a deleted path that .gitignore now covers (task 75's landing passed every suite and died at the commit; finished by hand); the stage step now removes a deleted path from the index and adds the rest, and the selftest lands a candidate that deletes and ignores one file)
Verify: cd pyto && python -m unittest tests.test_use && ! grep -rn 'parallel branches, so none of them' USE.md README.md research/START-HERE.md LANDING.md
Allow: pyto/USE.md pyto/README.md pyto/research/START-HERE.md pyto/LANDING.md pyto/tests/fixtures/use pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
