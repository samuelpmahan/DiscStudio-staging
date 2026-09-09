# Open findings: Day 2, fixer round 1

Items a required fix named that this round could not close, with what remains and
who can close it. Everything else from round 1 is closed in the tree; see
`pyto/CHANGES.md` (Day 2 entry, "Fixer round 1 decisions") and the file:line list
in the round's report.

## 1. Every `commit.txt` still carries a `-dirty` suffix (round 1, finding 12)

**What the finding asked.** Re-run `run.py` and the three Day 2 scripts with
`--force` on a clean tree and confirm every `evidence/*/commit.txt` carries a bare
sha with no `-dirty` suffix, restoring the property Day 1 established for
`evidence/run-1` (commit 3f448df, "commit.txt carries a clean SHA").

**What was done.** All four evidence directories plus `evidence/replay/`,
`evidence/tamper/`, `evidence/determinism.log` and
`evidence/lf-source-drift.log` were regenerated from the current code, so no
evidence file is stale with respect to the sources beside it, and
`run.py`'s `commit_sha()` is behaving exactly as designed.

**What remains, and why this round could not do it.** The suffix is honest: the
fix round's own edits (`retain.py`, `replay.py`, `run_regrouped.py`,
`second_experiment.py`, `test_replay.py`, `test_retain.py`,
`test_second_experiment.py`) are uncommitted, and `WATCHED_PATHS`
(`run.py:55` = this experiment directory plus `pyto/src`) correctly reports them
as dirt. A bare sha is reachable only by committing those edits and re-running the
four scripts with `--force`, and this round is explicitly forbidden to `git
commit`. Gaming it -- narrowing `WATCHED_PATHS`, or excluding the fixer's own
files -- would remove the very check that makes the stamp worth reading.

**Close it by** (orchestrator, after this round is merged, on a clean tree):

    python3 experiments/grouped-ablation/run.py              --out evidence/run-1              --force
    python3 experiments/grouped-ablation/run_regrouped.py    --out evidence/run-2-regroup      --force
    python3 experiments/grouped-ablation/run_reinput.py      --out evidence/run-3-reinput      --force
    python3 experiments/grouped-ablation/run_from_retained.py --out evidence/run-4-from-retained --force
    python3 experiments/grouped-ablation/replay.py

then confirm every `evidence/*/commit.txt` is 40 hex characters with no suffix.
Only `commit.txt`, `timings.json`, `receipts.json` and each `retained.json`'s
`retained.commit` field should change (the last three are wall-clock or the sha
itself); a change anywhere else means the regeneration was not a no-op and must be
explained before the day closes.

## 2. Nothing here needs a second library change

No item in round 1 required a second edit to `pyto/src/pyto/`. The day's one
library seam remains the receipts seam in `pcr.py` (`pyto/CHANGES.md`, Day 2);
`retain.py`, `replay.py` and the run scripts are experiment-local, and
`json.dumps([asdict(t) for t in run.ticks])` is untouched by this round because
`pcr.py` is untouched by this round.
