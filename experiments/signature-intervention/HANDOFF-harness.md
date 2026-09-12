# Signature-intervention harness handoff

This is an opt-in, small-budget Node harness for comparing two isolated variant
directories. Each variant is expected to provide `src/runtime.js` and the source
modules it imports; the agreed optional instrumentation interface is:

```js
createStudioRuntime(initial, { signatureObserver(event) {} })
```

The primary timing worker calls `createStudioRuntime(initial)` with no observer.
The separate `signature` worker calls it with an observer and retains observer
events under `signature-work.json`; those measurements must not be treated as
primary timing. No arms are run simultaneously. Rounds alternate baseline/candidate
order (AB/BA), and retain raw per-workload samples for cold, warm, and each of the
six existing card-render edits. Equivalence retains both arms' receipts while
comparing JSON-visible results after deleting only the top-level `result.run`.
The separate signature pass also records first/second/third-repeat observer-event
counts and a cheap 25-mutation (24-slot eviction/revisit) receipt probe.

Run from the repository root:

```sh
node experiments/signature-intervention/run.mjs compare \
  --baseline experiments/signature-intervention/variants/eager \
  --candidate experiments/signature-intervention/variants/lazy \
  --out evidence/signature-intervention/run-01
node experiments/signature-intervention/run.mjs verify --out evidence/signature-intervention/run-01
node --test experiments/signature-intervention/harness.test.mjs
```

Outputs are write-once and sealed with `manifest.json`; source identity,
environment, harness hashes, contract, inputs, exact equivalence observations,
raw paired rounds, separate signature work, and review placeholders are retained.
The default budget is two paired rounds, two cold samples, eight warm samples, and
two samples per edit. This is measurement scaffolding, not acceptance, promotion, or
a claim about browser paint.
