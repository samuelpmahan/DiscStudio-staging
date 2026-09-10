# Task 57

Intent: chains inside a Tick: the owner, 2026-09-10: 'Calculations inside a Tick must be independent was added as a rule, while your existing ChainSpot program deliberately chains dependent Calculations inside a Tick. Your definition was the moment that sequence becomes inspectable.' The kernel stops refusing a Calculation that binds an earlier sibling's result; inside a Tick the Calculations are a sequence in declared order and the Tick boundary is where the sequence becomes inspectable; a Tick with no sibling reads may run at once, a Tick with them runs in order even under parallel=True; two siblings producing one address is still refused; the decision goes on pyto/questions.md in the owner's words
Starting point: 97f318d4ddc4d9b52162e1736171de2d7caafce5 (land(task-56): the frontier says what the second wave landed: FRONTIER.md's Landed adds gains one line each for tasks 48 (the JS runtime speaks the same schedule), 49 (oc, effects with receipts), 50 (effects on the page), 51 (CI runs to completion), 52 (USE.md, executed) and 55 (green on macOS and Windows), each named by the task's own intent line, so the one file that says what got built is complete at the end of the sprint)
Verify: cd pyto && python -m unittest tests.test_parallel tests.test_multi_into tests.test_use
Allow: pyto/src/pyto/pcr.py pyto/tests pyto/USE.md pyto/questions.md pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
