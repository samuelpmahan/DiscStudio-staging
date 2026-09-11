# Task 81

Intent: brain harness: experiments/brain shared harness (store over pxc, dataset/synthetic, oracle, bench, bracket/judge/decide, finding, map_part, navigate through pql), map module, backend package, brain extra in pyproject and neat copy-venv install of [drawing,brain]
Starting point: 077d3475e36922d52ab6bc437883dd9b634a75e5 (land(task-80): neat delta <a> <b>: the capability delta against cost of two landings, computed not noted: from each landing's receipt and git diff, capability gained (Calculations registered, user actions and controls added, behaviours verified) and cost (files, lines, new pages, new address roots, moved assertions, regenerated fixtures) per candidate, fn.neat.delta.evaluate pure over the two measurements, the Part px.exp.neat.delta.<a>.<b> under pyto/experiments/review/deltas, patterns per repository in a manifest; first record: 78 (a second page over the composer) against 79 (the composer refined))
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks pyto/pyproject.toml pyto/scripts/neat.sh
Candidate: 11 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/brain/CONTRACT.md
- A  pyto/experiments/brain/__init__.py
- A  pyto/experiments/brain/backend/__init__.py
- A  pyto/experiments/brain/example.py
- A  pyto/experiments/brain/harness.py
- A  pyto/experiments/brain/map.py
- A  pyto/experiments/brain/records/brain_example.json
- A  pyto/experiments/brain/store/backend.json
- A  pyto/experiments/brain/test_harness.py
- M  pyto/pyproject.toml
- M  pyto/scripts/neat.sh

```
pyto/experiments/brain/CONTRACT.md                | 122 ++++
 pyto/experiments/brain/__init__.py                |   6 +
 pyto/experiments/brain/backend/__init__.py        |   7 +
 pyto/experiments/brain/example.py                 | 125 ++++
 pyto/experiments/brain/harness.py                 | 724 ++++++++++++++++++++++
 pyto/experiments/brain/map.py                     |  19 +
 pyto/experiments/brain/records/brain_example.json | 119 ++++
 pyto/experiments/brain/store/backend.json         | 252 ++++++++
 pyto/experiments/brain/test_harness.py            | 340 ++++++++++
 pyto/pyproject.toml                               |   3 +
 pyto/scripts/neat.sh                              |   2 +-
 11 files changed, 1718 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.zcMQ5rbgXn) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain                48  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK

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
