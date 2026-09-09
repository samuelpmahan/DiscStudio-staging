# s3-synthetic: retained evidence that the S3 reference runs without the corpus

Retained on Day 1 (Lane D) for critic gap 12 of research/ULTRACODE-WEEK.md.

- `snapshot.json`: the synthetic S3 snapshot built by the reader-phase scratch
  probe `probe_reference.py` (scratchpad `synthetic-S3/snapshot.json`), copied
  byte-for-byte; sha256 `5d3fb4ae6e01b174d26e7fd7d6508f7192109ffd5cc5e8581b04d4c1836b9008`.
  One tee-rect ring and one diamond, one measured in-family member, one tee,
  two tee pixels. The probe's materializer PNGs are not retained (they are
  rendering output of `materialize_s3_neon.py`, not inputs to the PCR).
- `testimony.json`: `{pcr, ticks}` recorded by `reference/chainspot-quick-anno/s3.py`'s
  PCR on that snapshot (canonical `json.dumps(sort_keys=True, indent=2)`).
- `test_s3_synthetic.py`: 5 unittest tests. Run from the pyto root with
  `python3 -m unittest discover -s experiments/s3-synthetic -p 'test_*.py' -v`
  (scripts/check_all.sh does this for every experiments/* directory).

## Observed value (the gap 12 claim, corrected)

Gap 12 says the test should record testimony inputs `{'ledger': 'fn:accountRings'}`
(s3.py:73-89). The observed CheckBalance testimony is

```
{'ledger': 'fn:accountRings', 'tees': 'px:px.tees', 'teePx': 'px:px.tees.px'}
```

`ledger` is the one fn: edge (s3.py:85 binds the Part accountRings writes at
s3.py:79; PCR.calc rewrites it to ResultRef at src/pyto/pcr.py:112-116);
`tees` and `teePx` are unwritten Parts and are recorded as px: (pcr.py:147-149).
The test asserts the full mapping and the gap 12 subset separately.

Caveat documented in the test: `build_investigation` runs its PCR internally and
discards the PcrRun (s3.py:90), so testimony is observed by running the returned
PCR a second time; importing `s3` builds `StageInvestigation` paths only
(s3.py:20, investigation.py:29-37) and creates no files.

## sys.path

The test inserts `pyto/reference/chainspot-quick-anno` into sys.path because the
reference imports `investigation` and `pyto` as top-level names (s3.py:17-18).
This is the intra-repo insert experiments/CAPTURE.md allows and logs; the test
asserts the inserted path is inside the repository.
