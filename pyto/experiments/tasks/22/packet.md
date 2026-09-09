# Task 22

Intent: Everything is a Part: with observe on, each invocation's receipt is also written into the store under the reserved px.receipt segment, so PQL can read receipts like anything else; with observe off nothing is written; no Calculation may bind a px.receipt address; the testimony stays byte-identical either way
Starting point: 76bc3d2a51c0e5442a0e4e8f519fe7d01484e9f5 (land(task-11): Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test)
Verify: cd pyto && python3 -m unittest tests.test_receipts tests.test_materialize tests.test_semantics tests.test_first_class
Allow: pyto/src/pyto/pcr.py pyto/src/pyto/core.py pyto/src/pyto/pql.py pyto/src/pyto/materialize.py pyto/tests pyto/CHANGES.md pyto/viewer/RECORD.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} ReceiptInputNotRefused: the design constraint refuses only a declared `into`/produces under `px.receipt.`, so a Calculation may still *bind a receipt Part as an input* (a test does exactly that); if "no Calculation may bind a px.receipt address" was meant to cover reads too, the guard has to move from `into` to the whole binding map.
{?} ReceiptPreexisting: `run_record`'s inferred `preexisting` excludes only the receipt addresses *this* run wrote, so a receipt left in the store by an earlier run still reports `preexisting: true` when an invocation reads it -- correct by the letter of RECORD.md, but the owner may want no `px.receipt.` Part ever counted as preexisting.
{?} ReceiptNameSegments: the PCR name and the Tick name go into the address verbatim, so a name carrying a dot silently adds a segment (`ablation.grouped` -> `px.receipt.ablation.grouped.Fit.fit.all`) and a name carrying a space makes an address `address.check` cannot flag; slugifying in `receipt_address`, or constraining PCR/Tick names, is a rule I did not want to invent.
{?} ReceiptRerunOverwrite: the scheme has no run identity, so running the same PCR twice against one store replaces each receipt Part in place (one address, no history) and only the last run's receipts survive; adding a run id or an invocation index would keep both, at the cost of an address a reader can no longer predict from the PCR alone.
{?} EvidencePinsTheKernel: `check_all.sh` cannot be green under this Allow list -- the retained Day 1/2 evidence (`experiments/grouped-ablation/evidence/*/retained.json`) pins `sha256` of `src/pyto/core.py` and `src/pyto/pcr.py`, so *any* kernel edit fails 33 grouped-ablation tests (`provider_agrees`, `ensure_retained_record`) until the evidence is regenerated, and `experiments/grouped-ablation/` is not on the Allow list; I verified the only difference in a fresh Day 1 record is those two module digests, and that `replay.py --force` alone does not fix run-2-regroup (its own retained.json pins them too). Also worth knowing: running the suites leaves `evidence/disc-stats-sidecar.json` modified in the working tree; I restored it rather than commit it.
{?} ReceiptStoreSetUnguarded: the refusal lives in the binder (`PCR.calc`/`Tick.calc`), not in `PxC.set`, so anything holding the store can still write a forged Part under `px.receipt.` -- consistent with `address.py` describing and enforcing nothing, but it means the segment is reserved against programs, not against callers.
