# Task 66

Intent: the difference is computed before it is shown, and counting comes before mining: pyto/src/pyto/neat/diff.py registers fn.neat.diff.candidates (two PQL documents and a seed store in, px.exp.blok.diff.<a>.<b> out: structural same or different, each output same, changed or new by value digest, and the remainder no calculation settled; documents with oc. calls are not run and say so); neat diff prints it and keeps the Part under pyto/experiments/review/diffs; pyto/experiments/molecules/transitions.py registers fn.molecules.transitions (every run record's invocation-to-invocation and Part-to-invocation transition counted, px.exp.molecules.transitions, stable order) and report.md opens with the count table before any molecule
Starting point: c0368114ed2864f030f0f5d19b03d23d4cfef34f (board: **started** `task-65`: the question loop as Parts and Calculations: pyto)
Verify: cd pyto && python -m unittest tests.test_neat_diff && python -m unittest discover -s experiments/molecules -p 'test_*.py' && python experiments/molecules/mine.py --check
Allow: pyto/src/pyto/neat/diff.py pyto/src/pyto/neat/__init__.py pyto/tests/test_neat_diff.py pyto/tests/fixtures/blok pyto/scripts/neat.sh pyto/experiments/molecules pyto/experiments/review/diffs pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} DiffNewIsAsymmetric: the outputs vocabulary (same/changed/new/unknown) has no fifth word for "removed", so an address only one of the two documents declares as `into` -- on either side -- is reported "new" rather than told apart by direction. Every fixture here has matching address sets on both sides so this never actually fires; worth a direction-aware word if a future diff compares documents that genuinely add or drop an address.
{?} DiffPrintForm: the CLI prints the diff value pretty (two-space indent, sorted keys -- px.py's own meaning of "canonical JSON" for a value meant to be read) while the sha256 inside the written Part hashes the compact, no-whitespace form (retain.py's canonical_json/digest_of, reused for the digest only). "Prints the diff value as canonical JSON" could mean either spelling; I kept the two uses separate rather than picking one JSON style for both.
{?} NeatDiffCalculationRunForm: `fn.neat.diff.candidates` is registered in a PxC and invoked with `pxc.call(...)` (USE.md section 3's plain form), not run through a PCR of its own with observe=True; only the two document sub-runs it triggers are `PCR.run(..., observe=True)` and materialized (the two records the packet asks for beside the Part). A more literal reading of "every Calculation runs through an observed PCR" would also wrap the comparison step itself, leaving it a receipt too.
{?} DiffRemainderOcOrder: the remainder lists every label (a's then b's) followed by one "not run: <call> is oc." line per oc. call found, in encounter order (a's Ticks then b's), not deduplicated -- a document naming the same oc. call twice gets two identical lines. Not specified either way in the packet.
{?} LabelsOutsideReadPqlGrammar: documents here carry a top-level `labels` list the JS `readPql` grammar (pql_document.py's own docstring) does not define; treated as this module's private, presentation-only extension and stripped before `structural_digest`/`run_document` see the document. Untested against the real reader, which would presumably just ignore the unknown key.
