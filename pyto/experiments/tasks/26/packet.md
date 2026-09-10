# Task 26

Intent: Ticks as circuits: tick_laws.py checks any pyto-run-record@1 against the node law (inside a Tick no Calculation consumes a sibling's produce, no two siblings produce one Part) and the loop law (nothing consumes a Part produced later), and reports total work versus critical path per Tick; no kernel change
Starting point: 71e2cbb57866744c6fd1b16665a30fb5844c03fd (root: {?} TicksAsCircuits, the owner's series/parallel question with the mapping as default)
Verify: cd pyto/experiments/tick-laws && python3 -m unittest discover -s . -p 'test_*.py' && python3 tick_laws.py --check ../grouped-ablation/evidence/run-1/record.json ../students/evidence/run-1/record.json
Allow: pyto/experiments/tick-laws pyto/scripts/check_all.sh pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
