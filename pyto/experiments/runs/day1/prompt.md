# Day 1 brief (verbatim from research/ULTRACODE-WEEK.md at 3b91d83)

Copied by Lane D per experiments/CAPTURE.md. Section boundaries: "### Day 1" (plan line 13) up to "### Day 2" (line 37); critic amendments naming Day 1: gaps 8, 12, 13, 16, 17, 18 (lines 248-312), plus the seed note at line 198.

## Day 1 section

### Day 1: Land the grouped-ablation spine, pin the substrate with mutation-verified characterization tests, start the run record

**Goal.** Turn scratchpad/ablation_spike.py into pyto/experiments/grouped-ablation with module-function Calculations in an explicit registry, testimony proving every fit/score invocation consumes 'fn:split', a retained failed variant, and a baseline saved-work ledger; make `python3 -m unittest discover -s tests -v` run all six existing checks (today 3: tests/test_first_class.py holds bare functions, pytest absent) plus ~14 characterization tests for the fail-loud/silent rules found by scratchpad/probe_rules.py; retain the day's own multi-agent run under CAPTURE.md. No file under pyto/src is modified.

**Deliverables.**

- pyto/experiments/grouped-ablation/features.py, calculations.py (REGISTRY of 5 Calculation objects, no lambdas), program.py (build_program + experiment-local family() helper), timing.py, run.py, test_grouped_ablation.py, evidence/run-1/{testimony.json, comparison.json, comparison.md, timings.json, variants.json, failed-variants.md, mermaid.mmd, saved-work.json, commit.txt}
- pyto/tests/test_first_class.py rewritten as unittest.TestCase (same three assertions) plus assertions on PcrRun.results keys and CalculationTestimony.into for the fan-out example; pyto/README.md test line corrected
- pyto/tests/test_semantics.py: ~14 TestCase methods, each docstring citing the file:line it characterizes, each verified by a mutation that makes it fail
- pyto/experiments/CAPTURE.md (run-record contract) and pyto/experiments/runs/day1/{prompt.md, candidates/, verdicts/, diff.patch, tests.txt, mutation-kill.md, meta.json}
- pyto/scripts/check_all.sh v0: mkdir -p consumers/discstudio-card/data; library tests; experiments/*/test_*.py; consumer tests (18); experiments/disc-stats with PYTHONPATH=. (4); prints per-suite counts; exit non-zero on any failure

**Workflow shape.** Fan out (parallel, disjoint targets): A writes test_first_class TestCase wrap + results/into assertions; B writes test_semantics.py from probe_rules.py; C lands the spike as the experiment package; D writes CAPTURE.md + check_all.sh + the runs/day1 skeleton. Verify (adversarial): a mutation lens applies one-line library mutations in a scratch copy of src (never the repo) and requires each new test to FAIL against its mutation — a test that survives is rejected; a semantics lens checks the experiment testimony shows inputs['split']=='fn:split' on all 12 fit/score invocations and rejects any variant whose args key collides with a bound input name (pcr.py:159-160); a prohibition lens greps evidence JSON for 'lambda' and '<function', confirms `git diff --stat -- pyto/src` is empty, and confirms no 32,768-subset enumeration. Synthesize: merge survivors, run check_all.sh, write runs/day1 per CAPTURE.md; a completeness critic diffs the 'NOT verified by any test' list (pcr.py:33-56,86-96,109-123,151-164; core.py:18-19,33-34,58-71; pql.py:55-73) against test names and lists any rule still untested as missing rather than dropping it.

**Verification.**

```sh
cd /home/user/DiscStudio-staging/pyto && python3 -m unittest discover -s tests -v   # expect 6 + ~14 tests OK (was 3); python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py' -v   # OK; python3 experiments/grouped-ablation/run.py   # prints ranked table with drop_g3 first, failed variant flagged; bash scripts/check_all.sh   # exit 0 with per-suite counts (library, grouped-ablation, consumer 18, disc-stats 4); git diff --stat a4dc559 -- pyto/src   # empty
```

**Evidence retained.** experiments/grouped-ablation/evidence/run-1/* (testimony after JSON round trip, comparison table, timings, mermaid, saved-work baseline: 5 Calculations authored, N authoring lines, 16 invocations executed, wall ms); experiments/runs/day1/* including mutation-kill.md (rule, mutated line, test that caught it) and tests.txt (full discover -v output); commit SHA in both meta.json and commit.txt.

**Depends on.** Nothing beyond a4dc559 and the scratch material: scratchpad/ablation_spike.py, probe_rules.py, ablation/ (verified present this session).

## Critic note on the seed (plan line 198)

- {?} JoblibComparison: pypi is reachable through the proxy, so a joblib.Memory comparison is attempted once on Day 3; whether an installed third-party comparator belongs in the retained evidence or only the stdlib baseline does is left open.

## Critic amendments naming Day 1

### Gap 8 (medium-high): evidence would not survive scrutiny

**Gap.** Day 5 clean-venv parity: check_all.sh v0 (Day 1) runs examples with `PYTHONPATH=src` and the disc-stats suite with `PYTHONPATH=.`; run from the venv those examples import the repo src, not the wheel, so 'identical counts from the clean venv with PYTHONPATH unset' is false for the two example checks, and the isolation lens that 'greps the log for PYTHONPATH' flags the script itself. The script also does `cd pyto` (relative) but is invoked from cwd=/tmp.

**Amendment.** Day 1 v0 already: run examples with plain `python3 examples/basic.py` (pyto is importable from the editable install; the wheel later); resolve the pyto root from the script's own path. Day 5 v1: the isolation lens whitelists `PYTHONPATH=.` for disc-stats (intra-directory, names stats.py) and rejects any PYTHONPATH containing 'src'; editable-vs-wheel-diff.txt includes pyto.__file__ printed by each suite.

### Gap 12 (medium): required return lacks retained evidence (provenance lens would reject it)

**Gap.** Day 5 return G lists 'cross-PCR px: provenance loss' and 'disc-stats non-JSON values' as counterexamples, and the next-experiment section cites 's3.build_investigation running without the corpus'. All three rest on scratch probes (probe_rules.py P6, the disc-stats json.dumps TypeError probe, probe_reference.py) that no day retains, so generate_returns.py must either exit non-zero or cite files outside the repo.

**Amendment.** Day 1 test_semantics.py: add test_cross_pcr_consumer_records_px_not_fn (second PCR over the same PxC records 'px:' — writers map is per PCR, pcr.py:118-123). Day 2 retain tests: run consumers/discstudio-card/experiments/disc-stats/run_experiment.build through retain_run and assert external -> {digest, ref} sidecar and results digest None, retained as evidence/disc-stats-sidecar.json. Day 5 (or Day 1 lane D): retain probe_reference.py's synthetic S3 snapshot under experiments/s3-synthetic/ with a unittest that s3.build_investigation runs on it and records testimony inputs {'ledger': 'fn:accountRings'} (s3.py:73-89), so the next-experiment proposal cites a retained file.

### Gap 13 (medium): claims the plan makes that Day 1 does not test

**Gap.** {?} SilentRules says 'a non-Part binding source fails only at run' is characterized on Day 1, but the 16-test list has no such test (probe_rules.py: PQL accepted at PCR.calc, AttributeError at run, pcr.py:147-151). The entrypoint's 'what survives a table projection' (entrypoint:60) is answered only in scratch probe_projection.py. A failing calculation mid-run leaving earlier `into` writes in the PxC and no PcrRun (pcr.py:163-164) is untested yet matters for every replay claim (a failed replay dirties the PxC).

**Amendment.** Day 1 test_semantics.py: add test_non_part_binding_source_fails_at_run (mutation: isinstance check on binding source in calc), test_table_projection_drops_provenance (PxC.items() -> fresh PxC keeps address/value identity, loses producer; core.py:85-89), test_failure_mid_run_leaves_prior_writes (mutation: wrap run in a rollback). Raise the Day 1 count to 19 and align the goal text ('~14'), the spec ('16 = 22') and the kill criterion ('fewer than 12').

### Gap 16 (low-medium): opportunity from the maps with high value that no day uses

**Gap.** Kernel map verified `PCR.mermaid() == Pcr.to_mermaid()` for the same graph and ablation E's byte-identical S0 JSON; the plan reports E as a result only (correct per stewardship:75) but never retains the equality as an executable check, so {?} KernelMerge rests on scratch output.

**Amendment.** Day 1 test_semantics.py (or test_first_class): test_pcr_and_pcr_graph_emit_identical_mermaid using the fan-out example authored both ways (pcr.py:179-219 vs graph.py:116-151). Zero src change, hours, and it is the retained evidence Day 5's KernelMerge item cites.

### Gap 17 (low): self-imposed count vs brief prohibition

**Gap.** Thesis and refused list state seams 'land only after two experiment-local uses'; brief:28 forbids inventing a universal repetition count. Brief:26 asks for 'use beyond the originating example', which is a qualitative criterion, not a number.

**Amendment.** Reword in thesis, Day 4 gate and CHANGES.md: 'used beyond its originating example (cite both call sites)' with brief:26 as source; drop 'two'.

### Gap 18 (low): small accuracy issues the user will hit when running commands

**Gap.** (a) Day 2 verification `grep -c ... | # 0` exits 1 when the count is 0, failing under set -e; (b) Day 1 saved-work.json hard-codes 'calculations_authored': 5 while the Day 2 critic 'rejects prose counts'; (c) Day 1 Lane A cites README.md line 20 — the manual invocation is on line 19; (d) after the Day 2 seam, run.py's testimony.json = asdict(run) minus results gains an 'observations' key, so run-2+ testimony files differ in shape from run-1 while the byte oracle is defined on ticks only; (e) Day 5 extract_substructures 'over the graph PCR.mermaid() emits' implies parsing Mermaid text; (f) Day 5 'seed-manifest drift refreshed' overwrites a retention record of the original source.

**Amendment.** (a) use `! grep -q`; (b) len(REGISTRY) and wc -l computed at run time; (c) cite README.md:19; (d) define testimony.json as {pcr, ticks} and put observations in observations.json from Day 2; (e) operate on the retained program dict and assert node/edge sets equal what pcr.py:196-217 emits; (f) write seed-manifest-<sha>.json alongside rather than overwriting, or record the overwrite in CHANGES.md.

## Lane briefs as issued

Four lanes with disjoint targets (plan, Day 1 "Workflow shape"): A test_first_class TestCase wrap + results/into assertions; B tests/test_semantics.py from scratchpad probe_rules.py; C experiments/grouped-ablation from scratchpad ablation_spike.py (seed threaded explicitly; no lambdas; REGISTRY of module functions; leave-one-group-out only); D experiments/CAPTURE.md, scripts/check_all.sh v0, runs/day1 skeleton, experiments/s3-synthetic (gap 12). Hard rules for every lane: no file under pyto/src modified (git diff --stat -- pyto/src empty), no commits (the orchestrator commits), python3 -m unittest only (pytest absent), LF line endings for new files, cite file:line for every claim.
