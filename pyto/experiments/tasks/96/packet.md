# Task 96

Intent: brain/backend five more ops, one of them the bracket's winner made usable: pack and unpack (the array_store bracket chose base64 of the float64 buffer; the round trip is exact rather than close, because nothing becomes decimal text on the way), the reduced qr with r's diagonal pinned non-negative so two engines cannot disagree about a sign, convolve in full, same and valid, and interp clamped outside its samples the way numpy clamps - each with an oracle Part per engine against the named reference and benchmark Parts at three sizes, the finding that packing wins by how long the numbers are (1.8x on drawn float64, a loss on small round ones), and the map's stubs for what each deliberately does not do
Starting point: e3ed1924f43fdbd3f7410705484ff92f824f0170 (land(task-94): brain/stats and brain/data, the second wave: kolmogorov-smirnov one and two sample, the wilcoxon signed-rank test and the p-value beside a pearson correlation, all with a pure-python tail (birnbaum-tingey, hodges, the limiting kolmogorov) that matches scipy exactly; a third group-by engine npsort that sorts once and reduces whole columns with numpy cumsum and reduceat, entered as the third candidate of the group-by bracket; melt as pivot's inverse and describe_table, the one place the data vertical calls the stats vertical)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 10 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/backend/cases.py
- M  pyto/experiments/brain/backend/ops.py
- M  pyto/experiments/brain/backend/summary.py
- M  pyto/experiments/brain/backend/test_ops.py
- A  pyto/experiments/brain/records/brain_backend_convolve.json
- A  pyto/experiments/brain/records/brain_backend_interp.json
- A  pyto/experiments/brain/records/brain_backend_pack.json
- A  pyto/experiments/brain/records/brain_backend_qr.json
- A  pyto/experiments/brain/records/brain_backend_unpack.json
- M  pyto/experiments/brain/store/backend.json

```
pyto/experiments/brain/backend/cases.py            |   48 +
 pyto/experiments/brain/backend/ops.py              |  244 +-
 pyto/experiments/brain/backend/summary.py          |   24 +-
 pyto/experiments/brain/backend/test_ops.py         |   93 +-
 .../brain/records/brain_backend_convolve.json      |  751 ++++
 .../brain/records/brain_backend_interp.json        |  217 +
 .../brain/records/brain_backend_pack.json          |  187 +
 .../brain/records/brain_backend_qr.json            |  394 ++
 .../brain/records/brain_backend_unpack.json        |  292 ++
 pyto/experiments/brain/store/backend.json          | 4550 ++++++++++++++++++--
 10 files changed, 6391 insertions(+), 409 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.1XaveSEQhD) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               549  OK
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

{?} pack/unpack are the array_store bracket's winner as facade ops, and they are float64 only.
`unpack` refuses any other dtype by name rather than guessing. int64 and complex128 are the obvious
next two and each needs its own exactness oracle, so they are stubs in the map rather than a
`dtype` argument that half works.
{?} a packed Part is a string to everything above the facade: `materialize` still digests it as
text (cheaply - it is 11 bytes a number instead of 20) and PQL cannot answer "what shape is it"
without reading the shape field the op happens to write. The kernel half of this is in the map's
next list, not in this task.
{?} the packing boundary is a test, not a slogan: base64 of float64 is a flat 11 bytes per number,
json is as long as the decimal text. Packing wins about 1.8x on drawn float64 and LOSES on a table
of small round numbers. Both directions are asserted, so a later "just pack everything" change goes
red.
{?} qr here is the reduced factorisation only, and it refuses a matrix wider than it is tall. The
full q and a rank-revealing column pivot are a different job with a different oracle.
{?} convolve's py engine is the direct O(n*m) sum; scipy's engine is pinned to method="direct" so
that all three engines are the same arithmetic. An fft-based convolve would be a different backend
with its own oracle and its own tolerance, not a faster spelling of this one.
