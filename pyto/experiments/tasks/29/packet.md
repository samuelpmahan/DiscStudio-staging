# Task 29

Intent: students: Mean and Median run in one Tick as parallel branches (the default under WhatIsATick), the hand-off says the honest reason (a receipt is per Calculation; a Tick is a step), evidence regenerated, and tick_laws shows the first Tick where work exceeds latency
Starting point: 42c5c7b0b8f7503ad351cefc09c2cdbbaa8850ef (task 26 packet: ActualEdgeCoverage marked resolved by the result-read fix)
Verify: cd pyto/experiments/students && python3 -m unittest discover -s . -p 'test_*.py' && python3 grade.py --run evidence/run-1 --handoff HANDOFF.md && cd ../tick-laws && python3 tick_laws.py --check ../students/evidence/run-1/record.json
Allow: pyto/experiments/students pyto/experiments/tick-laws/README.md pyto/CHANGES.md pyto/experiments/tasks pyto/questions.md
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} MissingTickTestStillRemovesHistogram: the brief suggested the missing-Tick test drop the Stats line, but check 4 matches a Tick name as a substring of the whole hand-off and "Stats" also appears in the honest-reason paragraph and in a `{?}` line, so removing only the Stats bullet leaves check 4 passing; the test still removes the Histogram bullet, which is the only Tick name that appears exactly once. Either check 4 should test the "one line per Tick" list rather than the page, or the test stays on Histogram.

{?} HandoffConfessesTheOldReason: the new paragraph says in the student's voice that the earlier reason was wrong and names it, rather than silently replacing it. That is a claim about the student's own history, which a cold reader has no way to check and which will read oddly to a reader who never saw the five-Tick version; the alternative is to state only the honest reason. Left as the confession because the point of the experiment was that a cold read caught it.

{?} TickLawsReadmeQuotesLiveMicroseconds: the tick-laws worked example now quotes work_ms and latency_ms from the committed `evidence/run-1`, which change on every regeneration, and the paragraph says so in a trailing clause. Whether a README should carry numbers that go stale the next time anyone runs `homework.py --out evidence/run-1` is the owner's call; the alternative is to name only the inequality.

{?} TickReportsHaveNoNames: `tick_laws.analyze_record` reports Ticks by index only, so the new test has to map "Stats" to an index through the record's own tick list before it can assert on it. A `name` beside `tick` in each tick report would let a checker's caller say "the Stats Tick" directly, but `tick_laws.py` is outside this task's allow list and was not touched.
