# Signature intervention variants

This is an isolated Node experiment; the application runtime, review data and
neat items are unchanged.

## Arms

- `variants/lazy/src/runtime.js` is a source snapshot of the current runtime,
  with only import paths adjusted for its location and the opt-in probe added.
- `variants/eager/src/runtime.js` has the same source and memo Part shape, but
  computes `stable({ revision, inputs })` on every registered Calculation call.
  The existing `previousInputs` / `previousVerified` bookkeeping remains in
  place so the comparison includes the certification boundary and 24-slot ring.

SHA-256 (timed source snapshot):

- lazy: `8cdf9a1051141b750e59ddc7e307b69a4a7c12c9af2f7fa90d923000c6652ae6`
- eager: `e8c4eb9421a0d77c8812151b3a5f4417870aa03999660cb7dce142c31d72759`

The separate instrumented copies used by the signature worker retain the
observer and have fingerprints lazy `e9392996c06d62fd8fe3e6c6ee8795db506d7a0a779628219907dc7fc66bfe47`
and eager `51282c17b97c6eebe7c2549dc14bb3ae73469c27811ed91348a4297fab9f8a5f`.
The timed copies contain no observer hook and expose no instrumentation field.

Both arms intentionally resolve their non-variant imports to the shared source
tree; this keeps the intervention source-only. For arm provenance, pin the
shared dependency snapshot alongside the arm hashes: repository `HEAD` at
creation was `1fc144350aa748fd92b91ea6af5f2a653446ca45`, and the aggregate
SHA-256 of every tracked `src/**/*.js|mjs` and `pyto/**/*.js|mjs` file was
`9a9d85f1d25aea1202762ee24cce177775a39717900d16bd6350b40b5c813739`. Recreate
that aggregate with:

```sh
git ls-files 'src/**/*.js' 'src/**/*.mjs' 'pyto/**/*.js' 'pyto/**/*.mjs' | sort | xargs shasum -a 256 | shasum -a 256
```

## Instrumentation interface

Pass the instrumented copy's `createStudioRuntime(seed, { signatureObserver })`. The callback receives
`{ address, revision, serialized, serializedBytes, serializationMs }` for each
signature decision. A worker can aggregate callback count, serialized bytes,
and timing independently; the callback and clock read are entirely absent from
the default path. The returned `runtime.instrumentation.enabled` indicates
whether the probe is active.

## Verification

From `DiscStudio-render-experiment`:

```sh
node --test experiments/signature-intervention/variant.test.mjs
```

Result: 10 tests passed. The tests cover equivalent card output, unchanged
reuse, mutable-input correctness, first/second/third-call certification,
24-slot eviction and revisit, observer data, disabled-by-default behavior, and
JSON/SVG output neutrality between plain and observed copies.
