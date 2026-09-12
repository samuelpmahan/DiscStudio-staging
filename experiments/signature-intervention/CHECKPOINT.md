# Signature intervention checkpoint

Status: measured, awaiting review. Timed source is observer-free. Source and
harness identities are checked before and after the run; both forks and harness
sources are copied into the sealed evidence.

`run-01-input-import-failure` and `run-02-zero-duration-incomplete` are kept;
neither is a performance result. `run-03` is the bounded completed run. Its
instrumented pass directly records avoided serializations; two timing rounds
only provide directional latency evidence. Its independently dispatched edited
worlds differ in event ID/time, so its edited rows are not equivalence evidence.
No default runtime change, UI/export change, deployment, acceptance, promotion,
or commit occurred.

Deterministic repair: `verification-05` seals shared captured worlds (including
explicit event IDs/times), both plain and instrumented source identities, full
per-arm `runRecord` receipts, and a PQL comparison Part. It passes 39/39
observations and plain-versus-observed neutrality. This adds no timing samples.

Parent review independently rechecked both final evidence seals and all 15
focused tests. Earlier runs are archived, preserving their contents, in
`evidence/signature-intervention/earlier-attempts.tar.gz`; their raw working copies
are outside the checkout at `/private/tmp/signature-originals.opWwUw`.
See README for exact review routes, command and timing/identity limitations.
