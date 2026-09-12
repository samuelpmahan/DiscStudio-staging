# Signature-avoidance intervention

This local Node experiment isolates one cause: the timed `lazy` arm is the
current signature expression, while `eager` always serializes the same inputs.
Both retain the same immutability proof and memo-ring/render behavior. Separate
instrumented copies count signature work and are never used for latency timing.

`run-03` is sealed at `evidence/signature-intervention/run-03`. It used two
sequential AB/BA paired rounds, two cold and eight warm samples per fixture,
with distinct dirty and warm edit cohorts. It is directional fixture evidence,
not a whole-app or browser-paint claim.

The unedited returned JSON-visible outputs and SVG hashes agree. `run-03`'s
edited rows were generated separately by each arm, and `dispatch()` creates an
event ID and time that become part of the world. Their differing input digests
therefore establish differing edited inputs, so those rows are not parity
evidence. A later deterministic verification capture must supply the same
explicit event values to both arms. Do not infer universal confidence or
promotion. `evidence/signature-intervention/verification-05` corrects this
with one captured set of explicit event values: PxC/PQL comparison passes all
39 first/second/third-repeat and edited observations, retaining both runRecord
receipts. Its separate observed pass confirms output neutrality and counts
eager 892 versus lazy 835 serializations (8,798,702 versus 7,377,414 bytes).

## Review and reproduce

From this repository root, using Node >=22 and a new output directory:

```sh
node experiments/signature-intervention/run.mjs deterministic-verify --baseline experiments/signature-intervention/variants/eager --candidate experiments/signature-intervention/variants/lazy --out evidence/signature-intervention/my-verification
```

Read `verification-05/pql-comparison.json`, `instrumentation-neutrality.json`,
`captures.json` and the two `*-work.json` files. Each arm performs 892 observed
signature decisions on the shared captures: eager serializes all 892; lazy
serializes 835. The latter writes 1,421,288 fewer serialized bytes (about 16.2%).
These counts support the proposed mechanism for these inputs; they are not a
general speedup claim.

`run-03/metrics.json` retains the two paired timing rounds separately from this
repair. Its seven unedited warm workloads favor lazy; cold results and the
uncontrolled edited workloads are mixed. Do not use the edited timing rows as
a strict same-input causal comparison.

The CLI's exit status indicates completion, not acceptance or necessarily
equivalence: inspect the comparison's `pass` and neutrality results. `verify`
checks the evidence seal only. `run-03` and `verification-05` were independently
rechecked, and all 15 focused tests passed during parent review. Standard app
tests/build are recorded with the subsequent integration verification.

Earlier incomplete/superseded runs remain intact in `earlier-attempts.tar.gz`.
The compressed archive passed `gzip -t`; uncompressed duplicates were moved to
`/private/tmp/signature-originals.opWwUw`, not deleted. Their old directory names
are historical labels, not diagnoses. In particular, the numeric-summary bug
also rejected legitimate zero/negative improvements; the corrected helper
distinguishes signed improvements from nonnegative timing samples.
