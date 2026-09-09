# Open findings: Day 2

One section per fixer round. Items a required fix named that the round could not
close, with what remains and who can close it. Everything else is closed in the
tree; see `pyto/CHANGES.md` (Day 2 entry) and each round's report.

## Round 1

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

**Close it by** (orchestrator, on a tree whose only uncommitted change is
`evidence/`). Round 3 removed the half of this that no amount of care could fix:
the stamp now excludes the whole `evidence/` tree, not just the one directory being
written (`run.evidence_excludes`, `run.py:235-265`), so regenerating run-2 after
run-1 no longer sees run-1's fresh output as dirt. What is left is honest and
unavoidable: uncommitted edits to producing code -- `run.py`, `retain.py`,
`replay.py`, `second_experiment.py`, the three `run_*.py`, `program.py`,
`calculations.py`, `features.py`, anything under `pyto/src` -- still stamp
`-dirty`, and a round forbidden to `git commit` cannot clear that.

    python3 experiments/grouped-ablation/run.py               --out evidence/run-1               --force
    python3 experiments/grouped-ablation/run_regrouped.py     --out evidence/run-2-regroup       --force
    python3 experiments/grouped-ablation/run_reinput.py       --out evidence/run-3-reinput       --force
    python3 experiments/grouped-ablation/run_from_retained.py --out evidence/run-4-from-retained --force
    python3 experiments/grouped-ablation/replay.py --force

`replay.py` now takes `--force` and refuses to write over its own committed
artifacts without it (`replay.OWNED_EVIDENCE`, `replay.py:1328-1400`), the way the
run scripts always have; it also regenerates the refusal logs under
`evidence/replay/refusals/` and the two `evidence/tamper/mutating-baseline-*`
files, which used to exist only because a test wrote them.

Run in that order (run-1 first: runs 2-4 quote its `receipts.json` durations). Then
confirm every `evidence/*/commit.txt` is 40 hex characters with no suffix. If any
still carries `-dirty`, run

    python3 -c "import sys; sys.path.insert(0, 'experiments/grouped-ablation'); import run; print(run.dirty_paths(exclude=run.evidence_excludes()))"

which prints exactly the non-evidence paths responsible.

**What may change, exhaustively.** Everything below is wall-clock or the sha
itself; a change anywhere else means the regeneration was not a no-op and must be
explained before the day closes.

| file | fields that may differ |
| --- | --- |
| `evidence/*/commit.txt` | the whole file (HEAD, plus `-dirty`) |
| `evidence/*/retained.json` | `retained.commit` only |
| `evidence/*/timings.json` | `timings[*].wall_ms` |
| `evidence/*/receipts.json` | `started_ms` and `duration_ms` of each receipt, and nothing else (`test_second_experiment.py::ReceiptsDeterminism` parses both, drops exactly these two keys and requires the remainder equal) |
| `evidence/run-1/saved-work.json` | `wall_ms` (its three `make_data`/`build_program`/`pcr.run` entries) and `wall_ms_total` -- Day 1's ledger carries wall clock, unlike runs 2-4's |
| `evidence/run-{2,3,4}*/saved-work.json` | `ms_saved` and `ms_saved_by_invocation`, which are run-1 receipt durations read back |
| `evidence/run-{2,3,4}*/interpretation.md` | the one `ms saved (...)` line, which quotes that number |
| `evidence/replay/*.log` | the `record:`/`cwd (outside repo):` paths and the per-source `sha256` rows; `replay.oracle_lines` names the lines that must NOT move |

## 2. Nothing here needs a second library change

No item in round 1 required a second edit to `pyto/src/pyto/`. The day's one
library seam remains the receipts seam in `pcr.py` (`pyto/CHANGES.md`, Day 2);
`retain.py`, `replay.py` and the run scripts are experiment-local, and
`json.dumps([asdict(t) for t in run.ticks])` is untouched by this round because
`pcr.py` is untouched by this round.

---

## Round 2

What the round-2 findings asked for that this round did **not** apply, and why.
Nothing here is silently dropped: each item names the exact edit, the file:line it
belongs at, and the rule that stopped it. Every line number below was checked
against the file as it stands, and the pcr.py mapping was computed by diffing
`git show d9dded6:pyto/src/pyto/pcr.py` against the current `src/pyto/pcr.py`
(difflib line correspondence), not typed from memory.

## 1. `provider_identity` is module-granular, and stays that way this day

Finding 3 offered two fixes. **(b) was taken**: the limitation is now stated in
`retain.provider_identity`'s docstring (`experiments/grouped-ablation/retain.py:423-437`)
the way `pyto.pcr.FrozenCalculation.limitation` states its own (`src/pyto/pcr.py:92`),
and the attack is an executable test —
`test_replay.py::ProviderIdentityIsModuleGranular`, which proves the forged provider
block is byte-identical to the honest one, that `verify_provider` agrees with it, and
that the record is refused anyway, by the result digests.

**(a) is open.** Recording a per-function identity — the
`sha256(inspect.getsource(callable))` the Day 2 seam already computes for
`FrozenCalculation.implementation_sha256` (`src/pyto/pcr.py:152-160`) — would make an
address that points at a different function of the same module disagree, and would
turn that forgery into a provider refusal rather than a digest one. It is not taken
here because it changes the `provider.registry` shape in **every** retained record
(`evidence/run-{1,2-regroup,3-reinput,4-from-retained}/retained.json`), and the
child's own `calculations_source_matches_record` check
(`replay.py` CHILD_REPLAY_SNIPPET) is written around all addresses sharing one
source digest. That is a lane-B/lane-D re-cut, not a fix to a finding.

## 2. Stale `pcr.py:<line>` citations outside this round's permitted file set

The Day 2 seam moved everything below `pcr.py:78` by roughly +150 lines (and the
`Tick`/testimony dataclasses by +4). Every citation inside
`experiments/grouped-ablation/` and `tests/test_receipts.py` was corrected this round.
The files below carry stale ones and are **outside the files this round may edit**;
each row is `<file>:<line>  <current text> -> <correct text>`.

### tests/test_semantics.py (Day 1 suite)

    :310  pcr.py:109-110 -> pcr.py:258-259
    :312  pcr.py:109 -> pcr.py:258        :312  pcr.py:43  -> pcr.py:47
    :321  pcr.py:118-123 -> pcr.py:267-272
    :323  pcr.py:121 -> pcr.py:270
    :331  pcr.py:112-116 -> pcr.py:261-265
    :332  pcr.py:157 -> pcr.py:329
    :334  pcr.py:114 -> pcr.py:263
    :347  pcr.py:112-116 -> pcr.py:261-265
    :348  pcr.py:147-149 -> pcr.py:319-321
    :351  pcr.py:149 -> pcr.py:321
    :368  pcr.py:112-116 -> pcr.py:261-265   :368  pcr.py:46 -> pcr.py:50
    :369  pcr.py:147-151 -> pcr.py:319-323
    :372  pcr.py:113 -> pcr.py:262
    :384  pcr.py:43-44 -> pcr.py:47-48       :386  pcr.py:43 -> pcr.py:47
    :394  pcr.py:33-56 -> pcr.py:37-60       :395  pcr.py:162 -> pcr.py:334
    :397  pcr.py:162 -> pcr.py:334
    :409  pcr.py:33-56 -> pcr.py:37-60
    :427  pcr.py:159-160 -> pcr.py:331-332   :430  pcr.py:160 -> pcr.py:332
    :444  pcr.py:151-155 -> pcr.py:323-327   :447  pcr.py:151 -> pcr.py:323
    :448  pcr.py:156 -> pcr.py:328
    :460  pcr.py:91-96 -> pcr.py:240-245     :463  pcr.py:95 -> pcr.py:244
    :530  pcr.py:162 -> pcr.py:334
    :547  pcr.py:88 -> pcr.py:237            :550  pcr.py:88 -> pcr.py:237
    :598  pcr.py:179-219 -> pcr.py:380-420   :601  pcr.py:197 -> pcr.py:398

`tests/test_semantics.py:527` (round-2 finding 12's named example, "Mutation:
pcr.py:162 `results[invocation.id] = value`") is the `:530` row above: the statement
is now `src/pyto/pcr.py:334`.

Six citations there point at statements the seam **rewrote**, not merely moved, so
they need a reading rather than a renumber: `:410`, `:412`, `:505` cite
`pxc.set(invocation.into, value)`, now `board.set(invocation.into, value)` at
`pcr.py:336`; `:475`, `:478` cite `resolved_inputs[name] = pxc.get(source)`, now
`board.get(source)` at `pcr.py:320`; `:487`, `:490` cite
`pxc.register(invocation.calculation)`, now `board.register(...)` at `pcr.py:314`,
and `pxc.call` at `pcr.py:161` is now `board.call` at `pcr.py:333`; `:502` cites the
`161-164` publication block, now `pcr.py:333-336`. `board` is `pxc` itself unless
`observe=True`, so every claim still holds; only the names moved.

### tests/test_first_class.py (Day 1 suite)

    :68   pcr.py:98-133 -> pcr.py:247-282
    :149  pcr.py:112-116 -> pcr.py:261-265   (its `pcr.py:163-164` is now :335-336)
    :167  pcr.py:118-123 -> pcr.py:267-272
    :183  pcr.py:59-78 -> pcr.py:63-145      (PcrRun now ends at the trailing `receipts`)
    :189  pcr.py:162 -> pcr.py:334           (its `pcr.py:177`, the `return PcrRun(...)`, is now :378 and returns `receipts` too)
    :195  pcr.py:112-116 -> pcr.py:261-265   (its `pcr.py:156-157` is now :328-329)
    :208  pcr.py:172 -> pcr.py:373
    :222  pcr.py:161-164 -> pcr.py:333-336   :228  pcr.py:164 -> pcr.py:336
    :238, :241, :242  pcr.py:156 -> pcr.py:328
    :272  pcr.py:179-219 -> pcr.py:380-420

### experiments/CAPTURE.md and experiments/s3-synthetic/

    CAPTURE.md:33                     pcr.py:159-160 -> pcr.py:331-332
    s3-synthetic/test_s3_synthetic.py:18   pcr.py:112-116 -> pcr.py:261-265
    s3-synthetic/test_s3_synthetic.py:20   pcr.py:147-149 -> pcr.py:319-321
    s3-synthetic/test_s3_synthetic.py:125  pcr.py:147-149 -> pcr.py:319-321
    s3-synthetic/README.md:27              pcr.py:112-116 -> pcr.py:261-265
    s3-synthetic/README.md:28              pcr.py:147-149 -> pcr.py:319-321

`experiments/runs/day1/` also carries ~340 such citations. It is a **run record of
Day 1** — a frozen account of a tree that no longer exists — and must not be
renumbered against today's `pcr.py`.

## 3. `experiments/grouped-ablation/program.py` cannot be corrected this day

`program.py:4` (`pcr.py:99-133`) and `program.py:37` (`pcr.py:112-116`) are stale; the
correct targets are `pcr.py:247-282` and `pcr.py:261-265`. The edit was applied and
then **reverted**, because it breaks the day's own kill criterion: lane C measures
`program_lines_changed` as `git diff --numstat d9dded6 -- program.py calculations.py`
(`second_experiment.py:158-166`) and
`test_second_experiment.py::NoReconstruction::test_program_lines_changed_is_zero_for_all_three_runs`
requires 0. A comment-only edit still counts as two changed lines and turned all three
committed ledgers to `program.py: 4`. Renumbering these two comments is a Day 3 or
later job, once the "program.py is untouched since d9dded6" claim no longer has to
hold, or the measure is taught to ignore comment-only hunks — which would weaken it.

## 4. Still open from round 1, unchanged by round 2

`commit.txt`'s `-dirty` suffix (round 1 item 1) is still open and for the same
reason: round 2's own edits to `retain.py`, `replay.py`, `test_replay.py`,
`test_second_experiment.py`, `timing.py` and this file are uncommitted, and
`WATCHED_PATHS` (`run.py:55`) correctly reports them as dirt. `evidence/run-1/`,
`run-2-regroup/`, `run-3-reinput/` and `run-4-from-retained/` were all regenerated
in this round (runs 2-4 with `--force`, after run-1, so their `ms_saved` resolves to
the committed `run-1/receipts.json`), so no evidence file is stale with respect to
the sources beside it -- only the sha stamp is. The close-it commands in round 1
item 1 are unchanged and still the way to clear it.

## 5. Round 2 needed no library change either

`pyto/src/` is byte-identical across this round: `git diff --stat <round-2 base> --
pyto/src/` is empty. The day's one library seam remains the receipts seam in
`pcr.py`, and `json.dumps([asdict(t) for t in run.ticks])` is untouched because
`pcr.py` is untouched. No required fix in this round asked for a second one; item 1
above is the only place where a library-shaped change was *considered* (a
per-function provider digest), and it is a change to the experiment-local
`retain.py` record shape, not to `pyto/src/`.

---

## Round 3

Eight required fixes; what this round could not close, and who can.

## 1. `commit.txt` still carries `-dirty`, but for one reason instead of two

Round 3 took the fix finding 7 named: the `-dirty` judgement now excludes the whole
`evidence/` tree (`run.evidence_excludes`, `run.py:235-265`, used by `run.py:328`,
`second_experiment.py:184` and `:325`, and `replay.py:178`). Outputs are not code,
so a regeneration no longer marks the next run dirty on account of the previous
one's files. All four runs were regenerated in that order, plus every artifact
`replay.py --force` owns.

**What remains.** `git rev-parse HEAD` plus `-dirty` is still what the four
`commit.txt` files carry, because this round's own edits to `test_replay.py` and
`test_second_experiment.py` are uncommitted and this round is forbidden to `git
commit` -- and, at the time of writing, `pyto/src/pyto/materialize.py`,
`pyto/tests/test_materialize.py`, `pyto/viewer/adapters.js` and
`pyto/viewer/fixtures/` (a concurrent Day 3 line of work in the same tree) are
untracked under `WATCHED_PATHS` as well. That is the stamp working: the evidence
really was produced by code that is in no commit. The close-it recipe in round 1
item 1 above is unchanged and now sufficient -- run it once those files land.

`{?} EvidenceDirtiness` in `pyto/questions.md` records the decision the owner may
disagree with: an owner who wants a regenerated-but-uncommitted evidence tree to
read as dirt should delete `evidence_excludes` and accept a permanent `-dirty`.

## 2. Provider identity is still module-granular (round 2 item 1(a), unchanged)

Round 3 did not take the per-function provider digest either, for the reason round 2
gave: it changes the `provider.registry` shape in all four retained records and in
the child's `calculations_source_matches_record` check. It remains a lane-B/lane-D
re-cut. The forgery it would close is still caught -- by the result digests, now
also by the receipt digests -- and `test_replay.py::ProviderIdentityIsModuleGranular`
still proves both halves.

## 3. Stale `pcr.py:<line>` citations outside the permitted file set (round 2 item 2, unchanged)

`tests/test_semantics.py`, `tests/test_first_class.py`, `experiments/CAPTURE.md`,
`experiments/s3-synthetic/` and `experiments/runs/day1/` still carry the citations
round 2 tabulated. Round 3 edited none of those files and the table above is still
the correction list.

## 4. `program.py`'s two stale citations still cannot be corrected (round 2 item 3, unchanged)

`program.py:4` and `program.py:37` cite `pcr.py:99-133` and `pcr.py:112-116`; the
correct targets are `pcr.py:247-282` and `pcr.py:261-265`. Editing them breaks the
day's own kill criterion (`program_lines_changed == 0` against `d9dded6`), which
`test_second_experiment.py::NoReconstruction` enforces. Day 3 or later.

## 5. Round 3 needed no library change

`pyto/src/` is untouched by this round: the receipts seam in `pcr.py` is read
(through `PCR.run(pxc, observe=True)`, now also from the replay child) and never
edited, and `json.dumps([asdict(t) for t in run.ticks])` is unchanged because
`pcr.py` is unchanged --
`test_replay.py::ReplayObserveSeam::test_testimony_bytes_are_identical_with_observe_on_and_off`
asserts that through the replay path as well.

## 6. `CheckAllLeavesTheTreeClean` is sensitive to a concurrent writer

`test_replay.py::CheckAllLeavesTheTreeClean` runs the two evidence-writing suites in
a child interpreter and compares `git status --porcelain` for `evidence/` before and
after. That is exactly the property finding 1 asks for, and in a tree with one writer
it is exact. In a tree where another process is writing under `evidence/` at the same
time -- which happened once during this round, when a concurrent Day 3 session wrote
`evidence/run-1/record.json` and `evidence/run-1/ticks/` mid-run -- it reports that
foreign write as a failure. The test cannot tell the two apart, and making it ignore
untracked additions would blind it to the very thing it guards. Left as is; a
re-run on a settled tree passes.
