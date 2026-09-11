# Task 81

Intent: brain harness: experiments/brain shared harness (store over pxc, dataset/synthetic, oracle, bench, bracket/judge/decide, finding, map_part, navigate through pql), map module, backend package, brain extra in pyproject and neat copy-venv install of [drawing,brain]
Starting point: 077d3475e36922d52ab6bc437883dd9b634a75e5 (land(task-80): neat delta <a> <b>: the capability delta against cost of two landings, computed not noted: from each landing's receipt and git diff, capability gained (Calculations registered, user actions and controls added, behaviours verified) and cost (files, lines, new pages, new address roots, moved assertions, regenerated fixtures) per candidate, fn.neat.delta.evaluate pure over the two measurements, the Part px.exp.neat.delta.<a>.<b> under pyto/experiments/review/deltas, patterns per repository in a manifest; first record: 78 (a second page over the composer) against 79 (the composer refined))
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks pyto/pyproject.toml pyto/scripts/neat.sh
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} dataset/synthetic arity: CONTRACT.md lists `dataset(name, for_, columns, rows)` and
`synthetic(name, for_, seed, shape, kind)` without a store, while oracle/bench/bracket/finding/map_part
all take the store first. harness.py takes the store first for all of them and also binds every helper
as a `Store` method, so both spellings read: `harness.dataset(store, name, ...)` and `store.dataset(name, ...)`.
{?} store/<vertical>.json scope: `save(vertical)` persists the addresses THIS process wrote, merged over
whatever the file already held, rather than everything in the PxC. That is what keeps a vertical that ran
`load_store()` from writing the other verticals' parts back into its own file. It also means a part written
by another process and only read here is not re-saved.
{?} non-finite floats: a part value holding nan/inf round-trips through python's json but is not valid JSON
for a stricter reader. harness.jsonable lets it through and harness.close treats nan as matching nan; if the
sprint wants strictness, that is the line to change.
{?} the committed store/backend.json and records/brain_example.json hold wall-clock benchmark numbers, so
they differ byte for byte on every rebuild. They are receipts, not fixtures, and no test pins their contents.
