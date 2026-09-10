# Task 40

Intent: parallel you can see: the Tick viewer draws a Tick's Calculations side by side when they are parallel branches, prints the Tick's work and latency and the run's critical path, shows placement when the record carries it, and tick_laws names Ticks; the students record is the demo page
Starting point: 53d31d925730b00a954afb7524e4c024d1760ef5 (board: **started** `task-39`: parallel for real and budgets: PcrRun runs the Ca)
Verify: cd pyto && node --test viewer/test/*.test.mjs && cd experiments/tick-laws && python3 -m unittest discover -s . -p 'test_*.py' && python3 tick_laws.py --check ../students/evidence/run-1/record.json
Allow: pyto/viewer/tick-viewer.html pyto/viewer/tick-viewer.js pyto/viewer/embed.mjs pyto/viewer/test pyto/experiments/tick-laws pyto/experiments/students/README.md pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
