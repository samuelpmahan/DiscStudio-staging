# Card-render experiment checkpoint

2026-09-12. Sam authorized the lever, merge of 941f354 and agent review, then a
cohesive experimental candidate using Lunas. Parts & Calculations and scope were
defined in task.yaml/candidate.yaml before repairs. RESULTS.md is the handoff.

- Branch: `codex/card-render-experiment`, based on
  `941f3544f82f80f88c7228abec646b0889d575fa`.
- Original `DiscStudio-staging` checkout left unchanged at 338e8a2.
- Implemented: capture/profile/compare/pixel and verification tools; scoped neat
  equiv historical replay/attempt retention and hot timing/shape coverage repairs.
- Capture command succeeded and retained 26 reproducible reference outputs,
  concrete sample worlds, source snapshots, source/harness hashes and raw
  cold/warm timings in `evidence/card-render/baseline-941f354/`.
- Baseline source fingerprint:
  `a9420bf5dd113f739d01887de16f2942f67508198c281161b3d4ef3df73d57b7`.
- Review findings and executable future-writer repro: UPDATE-REVIEW.md.
- Two runtime candidates were measured and retained. The second stays on this
  experimental branch: 55.5% warm gain, 14.9% cold discImage regression. Both
  preserve 26/26 SVG/result observations; neither passes the fixed cold guardrail.
- 24/26 browser pixel pairs match despite identical SVG inputs. Repeatability
  remains unresolved, not silently called equivalent. Failed images are retained.
- Verification: 368 app/viewer tests, 108 neat tests, 18 executable-doc tests,
  432 painter-family + 8 card fixtures pass; build passes. Wheel-install doc
  failures and the successful editable-install rerun are both retained.
- Local commits separate neat repairs, lever/evidence, and runtime/review metadata.
  Final source `006ea2c656a567fc2499c52ee54a74162412a5e7` passes all five checks
  in evidence/card-render/verification-final; file hashes stayed unchanged and
  all retained evidence seals verify. The receipt is committed separately. No push,
  deployment, acceptance or promotion. Sam still chooses which pieces to keep.
- Do not add a third runtime candidate under this pilot's two-candidate bound.
  Unrelated LAB/concurrency/undo/general canonicalization findings are not fixed.

Bundled Node:
`/Users/samuelmahan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`.
Bundled Python:
`/Users/samuelmahan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.
No `node`/`npm` on the default shell PATH. Python Playwright is unavailable;
bundled JS Playwright and `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
were used for the retained pixel check. A temporary editable Python environment
is at `/private/tmp/neat-candidate-verify.QW63ve/venv/bin/python`; recreate it
with Python >=3.10 and `pip install --no-deps -e ./pyto` when needed.
