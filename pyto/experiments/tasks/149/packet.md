# Task 149

Intent: a record of big values is cheap and an array is an array: one canonical json dump per value instead of three, an ndarray digested from its dtype, shape and raw bytes (so it has a cache key at last) and carried as kind array with its buffer beside the record instead of 109 MiB of integers, no PNG encoded that cannot fit the cap, and the viewer reading the new kind
Starting point: a0b1b1c877246bd20f33fcb05a413f01e67fb1e0 (land(task-147): pyto study on a table that is not tiny: a seeded sample where the method's cost is quadratic, a refusal where a training fold is narrower than the fit, the separator and the hole spelling the caller's, the entry point callable in a fresh process, and USE.md section 11)
Verify: bash pyto/scripts/check_all.sh
Allow: pyto/src/pyto/materialize.py pyto/src/pyto/pcr.py pyto/viewer/RECORD.md pyto/USE.md pyto/scripts/bench_record.py pyto/tests/test_materialize.py pyto/viewer/adapters.js pyto/viewer/tick-viewer.js pyto/viewer/test/record_schema.py pyto/viewer/test/test_record_schema.py pyto/viewer/test/adapters.test.mjs pyto/viewer/test/render.test.mjs pyto/experiments/grouped-ablation/evidence
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} ArraySidecarWriter: the owner asked for the raw bytes when "write_record is given a sidecar
directory"; the bytes exist only where the values are, and write_record is handed a finished
document, so `run_record(values_dir=...)` writes them and write_record is unchanged. Undo is one
parameter moved.

{?} ArrayPreviewCap: the owner asked for "a small preview (first array_cap entries flattened)";
his own generation passes array_cap=250000, and under that reading every one of a render's 196,608
numbers is spelled back into the record (123 MiB, measured) and the kind buys nothing. The preview
is the first 200, and array_cap can only lower it. Undo is deleting one `min`.

{?} ArrayDigestIsNew: an ndarray result had no digest at all before (json.dumps refuses one), and
has one now, so a receipt written by a numpy run before today says null where one written after
says a sha256. No committed record or fixture carries an array value, so nothing here changed byte
for byte; a store of receipts kept outside this repository would see it.

{?} OverCapImageNote: an image whose PNG cannot fit the cap now carries a digest of its pixels
(mode, size, raw bytes) instead of a digest of the base64 that used to be built and thrown away.
No fixture carries an omitted image, so the old note's format was not pinned anywhere; the rule is
in RECORD.md.

{?} ModuleDigestEvidence: touching pcr.py changes the pcr.py sha256 that the Day 1 evidence pins
(`provider.pyto.modules`), so evidence/run-1..6, the replay logs, the tamper reports and the
disc-stats sidecar were regenerated through their own builders (replay.py --force, run_regrouped.py,
run_reinput.py, run_from_retained.py, run_cached.py -- never by hand). Their commit.txt now carries
the copy's sha with -dirty, which is what those builders stamp from a working tree.
