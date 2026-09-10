# Task 26

Intent: Ticks as circuits: tick_laws.py checks any pyto-run-record@1 against the node law (inside a Tick no Calculation consumes a sibling's produce, no two siblings produce one Part) and the loop law (nothing consumes a Part produced later), and reports total work versus critical path per Tick; no kernel change
Starting point: 71e2cbb57866744c6fd1b16665a30fb5844c03fd (root: {?} TicksAsCircuits, the owner's series/parallel question with the mapping as default)
Verify: cd pyto/experiments/tick-laws && python3 -m unittest discover -s . -p 'test_*.py' && python3 tick_laws.py --check ../grouped-ablation/evidence/run-1/record.json ../students/evidence/run-1/record.json
Allow: pyto/experiments/tick-laws pyto/scripts/check_all.sh pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Codex's own notes (kept as written)

## Evidence

- `python3 -m unittest discover -s pyto/experiments/tick-laws -p 'test_*.py' -v` — PASS, 10 tests.
- `python3 pyto/experiments/tick-laws/tick_laws.py --check pyto/experiments/grouped-ablation/evidence/run-1/record.json pyto/experiments/students/evidence/run-1/record.json` — PASS.
- Mutation check 1: replacing `if producers_here:` with `if False:` made the sibling-consume test fail.
- Mutation check 2: replacing `if len(ids) > 1:` with `if len(ids) > 2:` made the duplicate-producer test fail.
- `PYTHON=/workspace/scratch/f2ea76ad2141/DiscStudio-staging/.venv/bin/python bash pyto/scripts/check_all.sh` — BLOCKED/FAIL while reconstructing the authenticated checkout: connector `fetch_file` truncated some large baseline files (for example `experiments/grouped-ablation/replay.py`) and the nonbinary evidence closure is incomplete. The captured attempt is `evidence/check_all.txt`; it is not evidence that the baseline itself fails. It shows baseline tests are blocked because this connector reconstruction has no authentic `.git`, and three oversized PNG evidence files are unavailable through the connector binary limit.

## Uncertain

{?} ActualEdgeCoverage: Records often leave `actual_consumes` empty, so this tool deliberately cannot certify all declared or `fn:` dependencies as parallel-safe. It reports only observed actual edges.
{?} TimingSemantics: Run records provide invocation durations, not measured parallel scheduling; work and critical path are a Tick-model estimate, and unknown durations remain null.
