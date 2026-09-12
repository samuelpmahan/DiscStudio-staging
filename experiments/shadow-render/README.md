# Candidate first, reference alongside

An opt-in Node pilot on `codex/card-render-experiment`. It serves the preserved
lazy-signature candidate and checks selected requests against the preserved
baseline in a separate worker. It does **not** change Studio app defaults, export
behavior, or the implementations themselves. This is not a third optimization.

The workflow and Parts & Calculations were defined first in `task.yaml`.

## Try the smallest interaction

Use Node >=22, from the repository root; every output directory must be new:

```sh
node experiments/shadow-render/run.mjs --out evidence/shadow-render/my-run
```

The default checks requests 1, 4, 7, … with at most one reference check in flight.
The demo publishes each primary delivery immediately, then pauses **between**
requests to inspect its check. It writes `REPORT.md`, actual served SVGs, events,
summary, source identities, and immutable addressed Parts with execution evidence.

To see a controlled bad output cause a real switch:

```sh
node experiments/shadow-render/run.mjs --out evidence/shadow-render/my-control --negative-control
```

The first delivered SVG has a red NEGATIVE CONTROL banner. Its original primary
result is retained; the labelled `fn.exp.shadow.corrupt` Calculation produces a
separate Part. The reference disagrees, the discrepancy remains in the record,
and later requests in this session use the reference. The bad delivery is **not**
retroactively rewritten. A new session starts with its own policy and evidence.

Other bounded experiments:

```sh
# Compare every request, with a pause between requests.
node experiments/shadow-render/run.mjs --out evidence/shadow-render/my-checked --sample-every 1
# Issue subsequent requests before earlier checks finish; excess checks are skipped, not queued.
node experiments/shadow-render/run.mjs --out evidence/shadow-render/my-burst --sample-every 1 --burst
# Deliberately give the checker an unrealistic deadline. Unavailability is not agreement.
node experiments/shadow-render/run.mjs --out evidence/shadow-render/my-deadline --reference-timeout-ms 1
```

Exit 0 means the run completed without a reported disagreement/error, **not**
that every request was checked. Exit 2 means evidence was produced with an outcome
needing attention (including deliberate negative controls). Exit 1 is a harness
failure. All outcomes are retained; none records human acceptance.

## What the Parts say

Each session has a fresh `px.exp.shadow.s<id>` root. Under `requests.r<sequence>`:

| Part | Meaning |
| --- | --- |
| capture | Exact finite-JSON world/method/arguments and input digest, captured before awaiting work. |
| capacity | Reference availability/busy state observed when selection was made. |
| selection | Serving implementation identity, sampling decision and the routing state that justified it. |
| primary | Serving output and actual Studio execution/run record; may instead report an error. |
| delivery | What was released, by which implementation, still explicitly unverified when applicable. |
| reference | Independently executed reference output/receipt, or its failure. |
| comparison | Matched, mismatched, unknown, not sampled, over budget, unavailable, or reference-served. |

`routing.r<sequence>` is a fresh derived decision, not an overwritten hypothesis.
`fn.exp.shadow.summarize` queries the request Parts through existing PQL and reports
coverage. A successful check means agreement **for that request**, not confidence
in all inputs. Periodic sampling can miss rare or systematic failures.

Orchestration receipts retain actual calls, bindings, prefix membership and output
digests. Large values live in the already-retained Parts, rather than being copied
into every enclosing execution. Both original Studio execution receipts remain.

## API and implementation boundaries

`session.mjs` exports `ShadowSession`. Its `submit({world, method, args, label})`
promise resolves with the serving output before a sampled check completes.
`drain()` awaits outstanding checks when the consumer chooses; `summary()` reads
their current outcomes; `close()` drains and terminates the workers. Only one
serving request may be in flight per session. `onPart` exposes the retained
observations; the included CLI writes them to disk.

`model.mjs` defines the capture/select/compare/route/summarize Calculations on
the existing PxC/PQL board. `worker-peer.mjs` provides bounded worker calls.
`render-worker.mjs` invokes the existing `createStudioRuntime.card/scene` and
`runRecord`; it contains no new renderer. The primary preserves its own memo
state across requests; the reference starts a fresh baseline runtime each time.

The CLI validates the sealed source artifacts before and after a run, retains
its own source files/hashes and hashes shared dependencies. The lower-level API
accepts source descriptors supplied by its caller; callers must establish those
identities. This is local provenance, not hostile-process authentication.

The equality contract is exact JSON-visible output, excluding **only** the
top-level `run` execution receipt. SVG, dimensions, fields, warnings, card/scene,
standings and other returned values remain in the comparison. Cold/warm execution
traces legitimately differ and are retained separately. The baseline shares
rendering logic: it is not an exhaustive correctness oracle. Browser pixels are
not checked; the earlier rasterization-repeatability issue remains unresolved.

Checking is off the delivery dependency path, but it still consumes CPU/memory.
Transfers and evidence persistence also cost time. This pilot makes no new
whole-app latency claim and does not transfer the earlier warm microbenchmark
percentage to this wrapper. A background check cannot protect an output that
must be verified *before* release; such a consumer must wait before that release.

## Retained demonstrations

Under `evidence/shadow-render/`:

- `checked/`: all 26 requests matched, each after primary delivery.
- `control/`: one deliberately corrupted SVG, one mismatch, 25 later reference deliveries.
- `overload/`: 9 matched checks, 17 explicitly skipped because the reference was busy.
  Which requests fit that budget is scheduling-dependent; capacity is recorded.
- `deadline/`: one unknown check, then 25 reference-unavailable outcomes; all 26
  primary deliveries still occurred. The checker was terminated, not retried forever.
- `sampled/`: default periodic sampling; 9 matched, 17 not sampled.
- `verification/`: final source verification logs and exact tested commit.
- `visual-check/`: rendered PNGs of the deliberate bad delivery and the next
  reference delivery. Visual inspection only, not pixel equivalence.
- `initial-runs.tar.gz`: the earlier, verbose complete runs. No observations were
  deleted; their uncompressed working copies were moved to a temporary directory.
  Unpack the archive to inspect their own manifests. Initial stepwise evidence was
  about 168 MiB; referenced orchestration receipts reduced it to about 33 MiB.

The 12 focused tests include deferred-check delivery, frozen inputs, sampling,
budget exhaustion, disagreement/fallback, missing evidence, malformed primary
output, cross-input/source refusal, a real worker timeout and actual warm-primary
versus fresh-reference rendering. The final verification also runs the app/viewer,
neat, executable docs and painter compatibility suites plus the build.

Verified source: `30a1671fd60733fd1e3aabfb1876fca8b3288038`, clean at capture.
All 380 JavaScript tests, 108 neat tests, 18 executable-doc tests, 440 painter
fixtures and the build passed. The normal Python Playwright app suite was not run:
that package is absent from this environment. The separate two-image visual
inspection does not substitute for it. See `CHECKPOINT.md` for the handoff boundary.

Review question: Is this session-local switch the right response for experimental
previews, and which requests should earn checking first? The run's `review.json`
binds the exact evidence and leaves Sam's response, acceptance and promotion empty.
