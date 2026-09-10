# Task 26

Intent: Ticks as circuits: `tick_laws.py` validates `pyto-run-record@1` records, checks observed node and loop laws from actual consumes/produces, and reports work versus Tick-model critical path; no kernel change.
Starting point: `0ae4c75d1fb5e8bc0fec19f3d7db76b81026bd36` (`exp/26`).

## Evidence

- `python3 -m unittest discover -s pyto/experiments/tick-laws -p 'test_*.py' -v` — PASS, 9 tests.
- `python3 pyto/experiments/tick-laws/tick_laws.py --check pyto/experiments/grouped-ablation/evidence/run-1/record.json pyto/experiments/students/evidence/run-1/record.json` — PASS.
- Mutation check 1: replacing `if producers_here:` with `if False:` made the sibling-consume test fail.
- Mutation check 2: replacing `if len(ids) > 1:` with `if len(ids) > 2:` made the duplicate-producer test fail.

## Uncertain

{?} ActualEdgeCoverage: Records often leave `actual_consumes` empty, so this tool deliberately cannot certify all declared or `fn:` dependencies as parallel-safe. It reports only observed actual edges.
{?} TimingSemantics: Run records provide invocation durations, not measured parallel scheduling; work and critical path are a Tick-model estimate, and unknown durations remain null.
