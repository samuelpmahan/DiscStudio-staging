# Task 43

Intent: a class in a repo and the desk that teaches the tutor: classroom/make_class.sh builds a class repo and a student desk repo under a temp dir, lands the desk into the class graded by the class's verifier with a score, records the cold reader's answer and checks it mechanically, and tutor.py renders a tutoring page as a pure function of the desk's receipts, byte-identical on rerun
Starting point: 9cc413bafb37b07508a5a4ec4fb91efc49eb1006 (board: **started** `task-42`: the studio speaks the whole record: the site's PQ)
Verify: cd pyto/experiments/classroom && python3 -m unittest discover -s . -p 'test_*.py' && bash make_class.sh --selftest
Allow: pyto/experiments/classroom pyto/scripts/check_all.sh pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
