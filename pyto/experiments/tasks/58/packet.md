# Task 58

Intent: the laws read chains: tick_laws.py, px laws and the two reference readers stop calling a read of an earlier sibling a node-law violation; a Tick whose Calculations read earlier siblings is a chain (runs in order, its latency is the sum), a Tick with no sibling reads is parallel; a read of a later sibling and two siblings producing one address remain violations; the students and ablation records still pass
Starting point: dc62a1b08965a8f9d05ff23ac1b277ba2d616d69 (board: **started** `task-57`: chains inside a Tick: the owner, 2026-09-10: 'Cal)
Verify: cd pyto && python -m unittest tests.test_px && python -m unittest discover -s experiments/tick-laws -p 'test_*.py' && python -m unittest discover -s viewer/test -p 'test_*.py'
Allow: pyto/experiments/tick-laws pyto/src/pyto/px.py pyto/tests/test_px.py pyto/viewer pyto/experiments/students pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} ChainSuffixOnlyWhenChained: `px laws` prints `(N parallel, M chain)` on the node-law line, and `chain` on a `--times` Tick line, only when the record has at least one chain; a chain-free record prints exactly as before. Reason: `tests/fixtures/px/laws-*.txt` (the byte-for-byte expected output of the two committed records) sit outside this task's Allow line. If you want `(4 parallel, 0 chain)` on every record, drop the guard in `cmd_laws` and regenerate the three fixtures.
{?} ChainLatencyIsTheWholeTick: a chain Tick's latency is the sum of every duration in it (the Tick runs in order), not the longest path through the sibling-read graph; a Tick that mixes a chain with an independent branch counts as all-series, in tick_laws.py and in the viewer's critical path alike.
{?} SingletonCountsAsParallel: tick_laws.py classifies a Tick of one Calculation (and an empty Tick) as `parallel` (no sibling reads), so the students record counts 4 parallel; the viewer's `isParallelTick`/`isChainTick` keep requiring two Calculations for either badge, as before.
{?} LimitationLineUnchanged: LIMITATION never stated the old rule (it speaks of reads, writes and what parallel would buy) and is the first line of the three px fixtures, so it stays; the rule and the owner's sentence live in tick_laws.py's docstring and README.
{?} HandoffSentence: HANDOFF.md's "inside one Tick it claims none" stated the old rule, so one clause was added in the student's voice ("claims an order only where one Calculation reads another's result"); the rest of the page is left as the cold read caught it (questions.md, WhatIsATick).
