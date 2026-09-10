# Task 41

Intent: the px shell: a px command over records and stores: px ps, px ls, px cat, px diff, px laws, px receipts; PQL reads receipts as Parts; the store refuses writes under px.receipt except from a run; every command is a pure function of its inputs with byte-identical output tests
Starting point: 4474273d423e62ae84eb42f2f7a4a61a01cbf4e2 (board: **started** `task-40`: parallel you can see: the Tick viewer draws a Tic)
Verify: cd pyto && python3 -m unittest tests.test_px tests.test_pql tests.test_semantics tests.test_first_class
Allow: pyto/src/pyto/px.py pyto/src/pyto/pql.py pyto/src/pyto/core.py pyto/src/pyto/__init__.py pyto/pyproject.toml pyto/tests pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
