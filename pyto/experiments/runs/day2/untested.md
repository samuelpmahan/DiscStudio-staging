# Day 2 completeness critic

Source list: research/ULTRACODE-WEEK.md Day 2 "Deliverables" (plan lines
162-186) and "Evidence retained"; critic amendments naming Day 2 (gaps 3, 4,
9, 10, 12, 14, 18a, 18d, 19); research/lab-transfer-ledger.md "What this
changes in the week" (Day 2 paragraph). Compared against the working tree at
HEAD (commit db577cd) and the four final-round lens verdicts in
`verdicts/`. This file lists deliverables not present, kill criteria that
fired, and ledger numbers that do not trace to a retained file — kept as
open items, not dropped, per the Day 1 completeness-critic precedent.

## Deliverables from the plan: present / renamed / absent

| plan deliverable | status | evidence |
| --- | --- | --- |
| Library seam: `PCR.run(pxc, *, observe=False)` | present, **renamed by design** | `pyto/src/pyto/pcr.py:284`. The plan's sketch (`PcrRun.observations: Mapping[str, Observation]`) was superseded by `research/lab-transfer-ledger.md`'s correction: the seam transferred is the LAB Tick **Receipt**, not an invented Observation (`PcrRun.receipts: dict[str, Receipt]`, pcr.py:145). `pyto/CHANGES.md`'s Day 2 entry states the transfer sources; this is a documented deviation, not a missing deliverable. |
| `tests/test_observations.py` | **absent under that name**, present as `tests/test_receipts.py` | Same renaming as above; `grep -rn test_observations pyto/` returns nothing. `tests/test_receipts.py` (21 tests) carries the byte-equality tests the plan asked `test_observations.py` to carry (`TestimonyBytesUnchanged` class). |
| `experiments/grouped-ablation/retain.py` | present | `to_program`/`from_program`/`retain_run` all present; `ShadowedInputError` refusal at retain.py:138-143. |
| `run_regrouped.py`, `run_reinput.py`, `run_from_retained.py` | present | evidence/run-{2-regroup,3-reinput,4-from-retained}/ each has the Day 1 file set plus `saved-work.json` and `interpretation.md`. |
| `replay.py` + `test_replay.py` | present | `test_replay.py` has 58 tests; `evidence/replay/`, `evidence/tamper/`, `evidence/determinism.log`, `evidence/registry-hole.log`, `evidence/lf-source-drift.log` all present. |
| `experiments/runs/day2/*` | present (this record) | `prompt.md`, `verdicts/`, `diff.patch`, `tests.txt`, `meta.json`, `brief-cold-read.json`, `untested.md` (this file). |
| `CHANGES.md` started | present, **not empty** | The plan describes it as "started (empty semantic-flip section)" — the "Semantic flips" section is in fact empty ("None. Every seam so far is additive...", CHANGES.md line 8), matching the plan; the Day 2 entry itself is substantial (not "started" in the sense of a stub), which is a strengthening, not a gap. |
| `compare_local.py` (gap 4 amendment) | present | `experiments/grouped-ablation/compare_local.py`; used by `run_reinput.py`/`run_from_retained.py` for "invocations skippable by digest" per gap 4's amendment. |
| disc-stats sidecar retention (gap 12 amendment) | present | `experiments/grouped-ablation/evidence/disc-stats-sidecar.json` (+ its non-JSON sidecar `disc-stats-sidecar.external.px.synthetic.disc_history.json`) exists, keyed exactly as gap 12 specifies: `external['px.synthetic.disc_history']` is `{digest, ref}`, not a raw value, and `results == {'annotate': None}` because `distinct_discs_by_mold`'s tuple keys are not JSON-serializable. `test_retain.py`'s `DiscStatsSidecar` class (6 tests, including `test_result_digest_is_none_because_json_cannot_hold_tuple_keys` and `test_the_program_still_round_trips_through_the_registry`) asserts it. |
| `experiments/s3-synthetic/` (gap 12, Day 1-or-5 amendment) | present (Day 1 deliverable, re-confirmed) | `bash scripts/check_all.sh` shows `experiments/s3-synthetic 5 OK`; this was a Day 1/5 item, not Day 2's, so its presence here is a re-confirmation, not new Day 2 work. |
| `{?} SeamGate`, `{?} Telemetry` in open judgments (gaps 14, 19) | present, added by this record stage | `experiments/grouped-ablation/questions.md` (created this session); the project-root `pyto/questions.md` (added by a concurrent session) already points to `experiments/*/questions.md` for both labels' detail, so the two files are consistent rather than duplicative. |
| PYTHONHASHSEED matrix under `env -i ... python3 -s -P` (gap 3) | present | `evidence/determinism.log` rows use `-s -P`, not `-I`; independently reproduced in the determinism lens verdict (`verdicts/determinism.json`, "retained" list). |
| logged `sys.path.insert` of the intra-repo experiment dir (gap 9) | present | `evidence/replay/fresh-process.log` records `sys.path before`/`sys.path after`; the hidden-state lens verdict confirms the delta is exactly the one intra-repo insert (`verdicts/hidden-state.json`). |
| `result_sha256` with no `default=` (gap 10) | present | `pyto/src/pyto/pcr.py:161-176`; `ResultDigest::test_non_json_value_yields_none` and `::test_tuple_keys_yield_none` in `tests/test_receipts.py`. |

**Net: zero deliverables from the plan or its Day-2-naming critic amendments
are missing.** Everything the plan asks for is present, either under its
planned name or under the name `research/lab-transfer-ledger.md` substitutes
for it (Receipt for Observation, `tests/test_receipts.py` for
`test_observations.py`), with the substitution recorded in `CHANGES.md`.

## Kill criteria checked

- **Day 2's kill criterion** (`research/briefs/day2-brief.md:253,336`):
  regrouping or re-inputting must not require edits to `program.py` or
  `calculations.py`; a forced edit would be recorded as
  `evidence/run-*/RECONSTRUCTION-REQUIRED.md`. **Did not fire.**
  `find pyto/experiments/grouped-ablation -iname 'RECONSTRUCTION-REQUIRED*'`
  returns nothing, and `git diff d9dded6 -- pyto/experiments/grouped-ablation/program.py
  pyto/experiments/grouped-ablation/calculations.py` is empty (confirmed
  independently by the cross-verification lens, `verdicts/cross-verification.json`).
- **Day 4's kill criterion** (line 234, "keeps the one-Calculation form if
  the split changes any of the 7 existing card outputs") is a Day 4 item,
  not Day 2's; not checked here.
- **The day's hard rule** ("exactly ONE library change... lane A only") is
  not itself a plan-stated kill criterion but is treated as one by every
  lens: `git diff --stat d9dded6 -- pyto/src` names `pyto/src/pyto/pcr.py`
  alone in all four verdict files' "retained" sections. Held.

## Numbers in the ledgers not traceable to a retained file

- `experiments/grouped-ablation/run_reinput.py`'s `interpretation.md`
  claims the ranking was "verified across seeds 3, 11, 13, 99 in the
  completeness critic's checks" (cross-verification lens finding,
  `verdicts/cross-verification.json`). `grep -rn '13, 99' pyto/` matches
  only that file and `research/ULTRACODE-WEEK.md` line 464, itself prose,
  not a retained run. **No evidence file records a comparison under seeds
  3, 13 or 99** — only seed 11 (this run's own seed) is retained anywhere
  in `experiments/grouped-ablation/evidence/`. Listed as untraceable, per
  the cross-verification lens's required_fix: either retain a small
  `evidence/seed-sweep.json` from a test that runs the four seeds, or
  reword the sentence to cite the plan line as an unretained note.
- `run_regrouped.py`/`run_reinput.py`/`run_from_retained.py`'s
  `saved-work.json` field `input_parts_changed` is an **authored literal**
  passed into `second_experiment.saved_work` (`second_experiment.py:243`
  only sorts what it is given), not computed from the two retained
  records. For run-4 the literal (`['scratch.ablation.split']`) is
  incomplete: independently recomputing the changed-external-Parts set from
  `record_prior`/`record_this` gives
  `['input.ablation.rows', 'scratch.ablation.split']` (cross-verification
  lens finding). Listed as untraceable-to-measurement for all three runs,
  and as **wrong** (not merely unlabeled) for run-4.
- `second_experiment.py`'s `calculations_added` field is structurally always
  `[]` because it is computed against the CURRENT run's own registry
  (`sorted(REGISTRY)`), which by construction contains every address the
  run could have used. It is not a false number in any of today's four
  runs, but it cannot be traced to "computed at run time" in the sense the
  day's hard rule intends — it would read `[]` even on a day that added a
  Calculation (cross-verification lens finding; `required_fix` proposes
  diffing against the prior run's registry instead).
- Two per-invocation digest columns — `receipts.json[*].result_sha256` and
  `retained.json['results'][*]` — agree in all four evidence directories
  today (verified independently in three of the four lens rounds) but the
  agreement is not asserted by any test in the repository
  (`grep -rn result_sha256 --include=*.py experiments/ consumers/` returns
  nothing outside `pyto/src` and `tests/test_receipts.py`). Not wrong today;
  listed because nothing pins it, so a future divergence would show up as
  numbers that silently stop matching rather than as a test failure
  (hidden-state lens finding).

## Not counted as gaps (checked and found traceable)

- `saved-work.json`'s `ms_saved` / `ms_saved_by_invocation` — traced to
  `evidence/run-1/receipts.json`'s `duration_ms` field for the skipped
  invocation ids (cross-verification lens, independently recomputed).
- `program_lines_changed` (`{program.py: 0, calculations.py: 0, total: 0}`)
  — traced to a live `git diff --numstat d9dded6 -- program.py
  calculations.py`, re-run and asserted by `test_second_experiment.py:102-130`
  with a `git merge-base --is-ancestor` guard against a moving HEAD.
- `calculations_inherited` — traced to the calculation addresses actually
  present in each retained program (independently recomputed: 5/5/4).
- `determinism.log`'s hash values and `hash_randomization` flags, and the
  LF-converted-src row's four digests — all independently recomputed by
  the determinism lens and matched byte-for-byte.
- The regroup/reinput `interpretation.md` "largest |delta|" figures and the
  planted-|w|-per-group tables — recomputed exactly from `features.py`
  `TRUE_W`/`GROUPS`/`CROSS_GROUPS` by the cross-verification lens.

## Suite counts

Two tables, because this record was written before Day 2's third fixer round and
the counts moved. Neither is asserted as prose: the first is what `tests.txt`
in this directory holds, the second is a fresh `bash scripts/check_all.sh` run
pasted verbatim from its `== per-suite counts` block.

### As of this record (traceable to `tests.txt`)

| suite | tests | status |
| --- | --- | --- |
| library | 64 | OK |
| experiments/grouped-ablation | 170 | OK |
| experiments/s3-synthetic | 5 | OK |
| consumer | 61 | OK |
| disc-stats | 4 | OK |
| examples | 3 scripts | OK |
| art-registry-md | - | OK (regenerated, matches committed ART-REGISTRY.md) |

`ALL SUITES PASSED` (`bash scripts/check_all.sh`, exit 0). The separately
requested `python3 -m unittest discover -s tests -v` (64 tests, OK) is
prepended to `tests.txt` ahead of the `check_all.sh` output, so the file
still ends with `ALL SUITES PASSED` per `experiments/CAPTURE.md`, "How a day
closes".

### After fixer round 3 (re-run, 2026-09-09)

    == per-suite counts
    suite                         tests  status
    library                          93  OK
    experiments/grouped-ablation    211  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           73  OK

    ALL SUITES PASSED

Where the two differ, and why:

- `experiments/grouped-ablation` 170 -> 211. Round 3 added the tests its eight
  findings asked for: the evidence-is-never-rewritten checks and the log/report
  oracles (`test_replay.py::VerificationWritesNoEvidence`,
  `::CheckAllLeavesTheTreeClean`, `test_second_experiment.py::EvidenceIsNeverRewritten`),
  the receipts-from-the-child join (`::ReceiptDigestsFromTheChild`,
  `::ReplayObserveSeam`), the module-table check (`::ChildModuleTable`), the
  computed `input_parts_changed` (`::InputPartsChangedIsComputed`), the
  receipts.json determinism check (`::ReceiptsDeterminism`) and the
  retained-vs-receipts digest join (`::RetainedDigestsEqualReceiptDigests`), plus
  two in `test_grouped_ablation.py` for the `-dirty` stamp's new evidence
  exclusion (`::test_evidence_excludes_names_the_evidence_tree_and_nothing_else`,
  `::test_a_dirty_producing_file_still_stamps_dirty_with_the_evidence_excluded`).
- `library` 64 -> 93. **Not Day 2's.** Those 29 tests are `pyto/tests/test_materialize.py`,
  which arrived with a concurrent Day 3 line of work in the same tree
  (`pyto/src/pyto/materialize.py`, `pyto/experiments/grouped-ablation/materialize_run.py`,
  `pyto/viewer/adapters.js`). The Day 2 library seam is still exactly one file
  under `pyto/src` (`pcr.py`), and round 3 changed nothing there.
- `viewer` (73) is a whole suite that did not exist at this record. **Not Day 2's**
  either: it arrived with the same concurrent Day 3 work (`pyto/viewer/`, Node 22,
  `EXPECT_VIEWER` in `scripts/check_all.sh`). Its count is the one number in the
  table above that was still moving when this was written -- that session was
  adding viewer tests while round 3 ran, and `EXPECT_VIEWER` alternately lagged
  and matched them (71, 72, 70, 73 across consecutive runs). The row above is
  from the run in which it matched; a later run may show `viewer` FAIL with
  "expected exactly N tests, got N+1" until that session bumps its own pin. No
  Python suite is affected, and round 3 touched neither `pyto/viewer/` nor
  `scripts/check_all.sh`.
- `consumer` (61) and `disc-stats` (4) are unchanged, which is what
  `EXPECT_CONSUMER` / `EXPECT_DISC_STATS` in `scripts/check_all.sh` pin. Neither
  pin needed updating by round 3; no suite shrank. The suites round 3 grew --
  `library` and `experiments/grouped-ablation` -- carry no pin by design, so
  nothing in `check_all.sh` needed bumping for them either.

## Blockers for committing

None of the open findings above block a commit of the Day 2 seam itself:

- The day's hard rule holds under four independent verification passes:
  exactly one file changed under `pyto/src` (`pyto/src/pyto/pcr.py`), and
  `json.dumps([asdict(t) for t in run.ticks])` is byte-identical with
  `observe` on and off, for the Day 1 program and both consumer entry
  points (card and art).
- `bash scripts/check_all.sh` exits 0 with no suite shrinkage
  (`EXPECT_CONSUMER=61`, `EXPECT_DISC_STATS=4` both pinned and met).
- No kill criterion fired (no `RECONSTRUCTION-REQUIRED.md`, empty
  `program.py`/`calculations.py` diff).
- `git status --porcelain` is clean at record time except the files this
  record stage itself wrote.

One item was worth the orchestrator's attention before or shortly after
committing, since it affected what a THIRD reader of this evidence could
trust. **It is closed by fixer round 3** and the paragraph is kept, corrected,
rather than deleted, because it is what the record said at the time:

- ~~**`bash scripts/check_all.sh` (via `replay.ensure_retained_record`)
  rewrites 13 committed evidence files as a side effect of running the
  test suite**~~ (hidden-state and determinism lens findings). This record
  stage ran `check_all.sh` once for `tests.txt` and reverted the resulting
  evidence diff with `git checkout -- pyto/experiments/grouped-ablation/evidence/`
  so the working tree stays byte-identical to what `diff.patch` and
  `meta.json` describe.

  **Closed, round 3 finding 1.** Verification now writes into temp
  directories and compares against the committed files as oracles;
  `replay.ensure_retained_record` no longer writes `evidence/run-1/retained.json`
  at all, and the committed artifacts are regenerated only by the run scripts
  and by `python3 experiments/grouped-ablation/replay.py --force`. Running the
  affected suites now leaves `git status --short` empty for `evidence/`, which
  `test_replay.py::CheckAllLeavesTheTreeClean` asserts by running them in a
  child interpreter and reading `git status --porcelain` before and after. The
  13-file churn no longer happens.
