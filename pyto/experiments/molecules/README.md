# Molecules

SUBDUE over the committed pyto-run-record@1 files: one labelled graph (invocations by
Calculation address, Parts by address; `reads`, `writes` and declared-order `next` edges),
mined for substructures that repeat and pay for themselves in bits.  Each is a molecule: a
repeated chain of Calculations over Parts, emitted as SUBDUE's canonical form, a PQL document
that runs its first instance as one Tick of chained Calculations, and a PQL query
(`PQL.prefix`) that finds its Parts in a store.  Two label schemes are reported: `exact`
(full addresses) and `shape` (every Part is `part`, a Calculation is `fn/inputs->produces`).

Run: `cd pyto && python experiments/molecules/mine.py` rewrites `report.md`;
`python experiments/molecules/mine.py --check [path]` re-mines and exits non-zero if the
report differs by a byte, so the report is evidence, not a note.  Tests:
`python -m unittest discover -s experiments/molecules -p 'test_*.py'`.

The miner is `experiments/hiding-primitives/subdue.py` (Cook and Holder, JAIR 1994).  The
owner's sentence that named it, 2026-09-10: "The forcing function of molecular synthesis got
squashed for no observable reason."
