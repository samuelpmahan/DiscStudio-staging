# Shadow-render pilot handoff

## what-is

Local branch: `codex/card-render-experiment`.
Verified implementation: `30a1671fd60733fd1e3aabfb1876fca8b3288038`.
Later handoff commits contain only documentation and retained verification/visual
artifacts. No push, deployment, app-default change or human acceptance occurred.

The existing PxC/PQL board records captured inputs, source identities, policy,
selection, delivered output, independent check, comparison and derived routing.
Existing Studio runtimes do the rendering. The candidate retains its memo state;
the reference gets a fresh runtime. The checker is bounded to one in-flight call
with a deadline. A mismatch switches later requests in this session; the already
served output and both receipts remain available for review.

## e

All evidence is under `evidence/shadow-render/`:

- `checked`: 26 matched requests.
- `control`: one deliberate mismatch, then 25 reference-served requests.
- `sampled`: 9 matched, 17 not sampled.
- `overload`: 9 matched, 17 budget-exhausted; no growing work queue.
- `deadline`: one unknown, then 25 reference-unavailable; all deliveries retained.
- `verification`: 380 JavaScript + 108 neat + 18 executable-doc tests passed;
  440 painter fixtures and the build passed. Source hashes stayed unchanged.
- `visual-check`: the first served card visibly bears the deliberate red warning;
  the second is the reference card without that warning. These are inspection
  screenshots, not parity evidence or a full app browser test.

The normal Python Playwright suite was unavailable (package not installed).
The neat suite emitted file-handle ResourceWarnings and passed; logs are unchanged.
Earlier verbose observations remain in `initial-runs.tar.gz`, not discarded.

## a*

The reference is another implementation, not a correctness oracle. Sampling may
miss failures. Neither missing checks nor reference-served outputs count as
independently verified agreement. This wrapper has no measured whole-app speedup.
It does not settle the earlier browser-pixel repeatability discrepancy.

## what-is-next

Review `control/REPORT.md` alongside `control/events.json`: is session-local
fallback useful for experimental previews? Which inputs deserve checking first?
`control/review.json` binds the exact run and leaves the human response empty.

The bounded pilot is complete. A separate integration change could attach this
same session/Part stream to a preview consumer, keeping release-before-check versus
release-after-check explicit. No such UI or export integration is implemented here.
