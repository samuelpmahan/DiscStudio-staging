# Guided experiments: candidate results

2026-09-12 · `codex/card-render-experiment` · base
`941f3544f82f80f88c7228abec646b0889d575fa`.
The original staging checkout remains clean at `338e8a2`. Nothing pushed or
deployed; no human acceptance or promotion. Separate local commits let Sam
choose the neat repairs, experiment lever/evidence, and runtime candidate.

Commits: `fe9f9c9` neat repairs; `47ecdaf` lever/evidence;
`006ea2c656a567fc2499c52ee54a74162412a5e7` runtime candidate and review metadata.
The final verification ran all five named checks against that committed source:
all passed, changed-file hashes stayed unchanged, and all evidence seals verify.
The subsequent evidence-only handoff does not alter the tested application code.
This successful source verification does not override the failed performance
guardrail or incomplete pixel parity below.

## What I recommend keeping

| Piece | Capability gained | Recommendation |
| --- | --- | --- |
| neat equiv | Replay historical inputs, refuse missing earlier values, retain each attempt's witness. | Keep for review. |
| neat hot | Separate measured time, unknown time, complete shape and observed prefixes. | Keep for review. |
| Experiment lever | Capture → profile → compare through existing PxC/PQL; retain source, inputs, hypothesis, timings and unanswered review. | Keep the workflow; exact browser-pixel repeatability remains red. |
| Lazy signature reuse | Avoid repeated serialization of identical, proven-immutable inputs. | Hold as experimental: warm benefit but a cold guardrail failure. |

No new renderer, Part store, distributed execution framework or DSL.

## Two guesses, two retained results

The unchanged CPU profile repeatedly names `stable` serialization among its
hottest frames. That led to two bounded implementations of one hypothesis:

| Attempt | Warm broadcast paired-median improvement | Rounds exceeding 5% | Cold guardrail | Frozen verdict |
| --- | ---: | ---: | --- | --- |
| 01: eager immutable proof | 61.6% | 7/7 | Six workloads regress >10% | rejected-regression |
| 02: prove only on repetition | 55.5% | 7/7 | discImage regresses 14.9% | rejected-regression |

Attempt 02 is the runtime on this branch. Its warm broadcast round medians have
medians of 2.429 ms baseline and 1.070 ms candidate. The reported 55.5% is the
median of **paired ratios**, not the ratio of those aggregate medians. Likewise
cold discImage aggregates are 7.204 ms and 7.716 ms, with a 14.9% paired-ratio
regression. Inspect the seven raw pairs, not only averages.

Timing varies substantially between runs. Some early attempt-01 rounds overlapped
verification work; it is exploratory evidence, not a clean hardware-independent
latency estimate. These observations do not establish the cause of every cold
difference. We stopped at two candidate changes; no threshold was retuned.

Both candidates preserve **26/26 exact SVG and complete result-hash observations**,
including reuse traces. The existing 24-slot memo Parts and result lookup remain
unchanged. The second variant defers recursive proof until repetition. Mutable
values, shallow-frozen descendants and accessors keep the serialization path.
Tests cover mutation followed by freezing and memo-ring eviction too.

This measures Node runtime/SVG generation, not browser paint, app load, all
possible user worlds or ChainSpot CV accuracy.

## Pixels: useful failure

Chrome 152.0.7977.83, one browser, fixed viewport/device scale, page network
blocked: **24/26 exact pixel pairs**. Black/white negative control passed.
Failures: `card-showcase/warm` (1,017 differing pixels), `card-discImage/cold`
(2,206). Both pairs have byte-identical input SVGs. Browser rasterization/capture
therefore failed same-input repeatability; the precise browser cause is not
isolated. This is not evidence that the candidate generated different artwork.
Pixel equivalence stays unverified. Failed images and the earlier sandbox launch
failure remain retained. No tolerance was raised.

The next useful pixel experiment is a same-input repeatability control before
using browser differences to judge an implementation.

## Lunas and verification

One Luna owned replay/history; one owned measurement coverage; one tested the
harness. Parent review caught two incomplete first passes: unavailable earlier
writes still falling back to initial values, and truncated counts escaping into
exact per-element advice. Focused follow-ups closed both with regression tests.
A final read-only runtime review found no new correctness bug for supported
plain-data Studio inputs; its seven focused tests pass.

- App + shared viewer: **368/368**, including 9 harness and 7 signature tests.
- neat: **108/108**, including 33 equiv and 30 hot tests.
- Executable USE.md: **18/18** with this checkout installed editable in a local
  temporary Python environment. The earlier wheel-install run failed seven
  repository-fixture-dependent examples; its failed log is retained.
- Painter compatibility: **432/432 families + 8/8 cards**, byte-identical.
- Build passes; pre-commit source/test fingerprint:
  `c39aa73d0279249ad504be61fbb97d2dd11e1a93a07d9107a4f39557b297e0f1`.
- Normal Python Playwright app checks were not run: that package is unavailable.
  The JS pixel check does not verify controls, real storage reload or downloads.

USE.md's dense-output example now omits per-element advice because its initial
input's shape was not materialized. The docs were updated to the deliberate
coverage change, not the analyzer weakened to preserve the old expected output.

Source identity includes the commit **plus file hashes and patch**: an uncommitted
candidate is not its HEAD. Attempt 02 executable-source fingerprint:
`baba714e4bc2679d6f1b4d216d39930b880c8ebc87803569c013145e8097d4c5`.
Its runtime SHA is `b256a1b5d8dcc5e1ffd30dd397bd585ff773239d288670b3146a2cfbb282a13f`,
the same runtime on this branch. Later review-text changes do not alter retained
snapshots. Seals detect accidental drift, not hostile tampering/authentication.

## Evidence and one concrete review

Under `evidence/card-render/`:

- `baseline-941f354/`: concrete inputs, reference outputs, source, contract/env/hashes.
- `profile-941f354/`: CPU profile and hotspots.
- `attempt-01-signature/`, `attempt-02-lazy-signature/`: source, patch, round-N.json,
  comparison.json, composition.json, ordinary PxC Parts and unanswered review.json.
- `pixels-02-browser/`: report, paired PNGs, negative control, browser identity.
  `pixels-02/` retains the sandbox launch failure.
- `verification/`: combined logs, failed wheel doc run, source/patch and build.
  `verification-editable/`: successful 18-test doc rerun.
- `verification-final/`: final committed-source verification, including the
  painter fixtures. Read its source.json for the exact commit and result.json
  for the actual outcome; it does not include the separate pixel verdict.

`UPDATE-REVIEW.md` is the pre-repair audit. Unrelated LAB stale anchors,
shared-runtime concurrent renders, undo behavior, generic canonicalization and
hot multi-output input identity remain outside this repair bundle.

Open attempt 02's review.json beside its comparison and patch. The question is:
**is the repeat-render benefit worth the observed cold cost for this use, or do
we keep the tools/repairs and hold the runtime?** My recommendation is the latter.
Sam's answer refers to that exact attempt. A changed candidate gets a new
comparison and answer; no previous acceptance is copied forward.
