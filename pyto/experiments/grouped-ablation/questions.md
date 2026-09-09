# Open judgments: experiments/grouped-ablation

One `{?} Label: detail` entry per judgment left open by this experiment,
rather than silently decided one way or the other. Closed judgments (decided
and recorded) live in `pyto/CHANGES.md`'s Day 2 entry and in
`evidence/OPEN-FINDINGS.md`; this file is only the still-open ones.

- `{?} SeamGate` (research/ULTRACODE-WEEK.md critic gap 14;
  `docs/PYTHON-LAB-STEWARDSHIP.md:62`, quoted in the gap as `:53`: "No Pyto
  implementation starts until the consumer fixture establishes the
  calculation boundaries and the owner confirms which presentation/config
  values are external inputs versus calculation results"). The Day 2 receipts
  seam (`pyto/src/pyto/pcr.py`) is not the replay seam: it records digests
  and durations of what `PCR.run` already did and classifies no value as an
  external input versus a calculation result, so it decides nothing the
  precondition reserves for the owner (`pyto/CHANGES.md`, "What this seam is
  not"). Retention and replay stay experiment-local
  (`experiments/grouped-ablation/retain.py`, `replay.py`), not in
  `pyto/src`. `{?} ExternalInputBoundary` itself is not answered by this day
  and stays open for the owner.
- `{?} Telemetry: read/write receipts landed as PcrRun.receipts (observe=True
  only); failed-run PcrRun-instead-of-raise deferred` (research/ULTRACODE-WEEK.md
  critic gap 19). The transferable idea from the neat map — sequence-ordered
  read/write/invocation receipts and a failed-run `PcrRun` instead of a raise
  (`pxc.ts:26-62`, `pql.ts:470-479`) — is only partly transferred: `Receipt`
  covers one invocation's declared/actual consumes-produces, writes and
  timing (`pyto/src/pyto/pcr.py:96-127`), gated behind `observe=True`
  (default `False`, so a caller that never asks for receipts sees the d9dded6
  behaviour unchanged). Sequence-ordered read/write receipts across a whole
  run are not implemented. A failing invocation still raises and returns no
  `PcrRun`, so a failed run produces no receipts either;
  `tests/test_semantics.py`'s `test_failure_mid_run_leaves_prior_writes`
  (critic gap 13) characterizes the current behaviour this leaves in place.
