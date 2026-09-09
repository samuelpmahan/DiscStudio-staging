"""Retained synthetic S3 snapshot: s3.build_investigation runs without the corpus.

Critic gap 12 (research/ULTRACODE-WEEK.md, "Gap 12"): the next-experiment
proposal cites "s3.build_investigation running without the corpus", which until
now rested on the scratch probe probe_reference.py. This directory retains that
probe's synthetic snapshot (snapshot.json, byte-identical to the scratch file,
sha256 5d3fb4ae6e01b174d26e7fd7d6508f7192109ffd5cc5e8581b04d4c1836b9008) and
the testimony the reference PCR records on it (testimony.json, shape
{pcr, ticks} per gap 18d), so the claim cites files in the repository.

Observed (Day 1, this snapshot): the CheckBalance invocation's testimony inputs are

    {'ledger': 'fn:accountRings', 'tees': 'px:px.tees', 'teePx': 'px:px.tees.px'}

Gap 12 phrases the expected value as {'ledger': 'fn:accountRings'}; that is the
one fn: edge (reference/chainspot-quick-anno/s3.py:81-89 binds ledger=ledger, the
Part written by accountRings at s3.py:73-80, which PCR.calc rewrites into
ResultRef('accountRings') at src/pyto/pcr.py:112-116) but not the whole mapping:
tees and teePx are bound Parts nobody writes, so they are recorded as px:
(pcr.py:147-149). The tests below assert the full observed mapping and, separately,
the gap 12 subset.

Two facts about the reference that shape the tests:
- s3.build_investigation runs the PCR itself and discards the PcrRun (s3.py:90);
  testimony is only visible by running the returned PCR a second time, which
  re-publishes the same values into the same `into` Parts.
- Importing s3 constructs INV = StageInvestigation('S3', <reference dir>)
  (s3.py:20); that only computes paths (investigation.py:29-37) and touches no
  file, so the missing corpus and Node bridge never come into play.
"""

from __future__ import annotations

import dataclasses
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTO_ROOT = HERE.parents[1]
REFERENCE = PYTO_ROOT / 'reference' / 'chainspot-quick-anno'

# Intra-repo sys.path insert (logged per experiments/CAPTURE.md, "sys.path"):
# the reference scripts import 'investigation' and 'pyto' as top-level names
# (reference/chainspot-quick-anno/s3.py:17-18). The inserted path is inside this
# repository; cross-repository injection stays forbidden (docs/worktree-workflow.md:17).
SYS_PATH_INSERT = str(REFERENCE)
if SYS_PATH_INSERT not in sys.path:
    sys.path.insert(0, SYS_PATH_INSERT)
    print(f'[s3-synthetic] sys.path.insert(0, {SYS_PATH_INSERT}) intra-repo reference dir', file=sys.stderr)

import s3  # noqa: E402  (reference/chainspot-quick-anno/s3.py)
from pyto import PQL  # noqa: E402

SNAPSHOT_PATH = HERE / 'snapshot.json'
TESTIMONY_PATH = HERE / 'testimony.json'

OBSERVED_CHECK_BALANCE_INPUTS = {
    'ledger': 'fn:accountRings',
    'tees': 'px:px.tees',
    'teePx': 'px:px.tees.px',
}
OBSERVED_ACCOUNT_RINGS_INPUTS = {
    'rings': 'px:px.tees.rings',
    'family': 'px:px.tees.family',
}
OBSERVED_SUMMARY = {
    'enclosed': 2,
    'diamondDropped': 1,
    'elongated': 1,
    'excludedByBadge': 0,
    'candidates': 1,
    'measured': 1,
    'unframed': 0,
    'votedOutOfFamily': 0,
    'familyMembers': 1,
    'tees': 1,
    'teePx': 2,
    'balanced': True,
}


def load_snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text())


def testimony_of(run) -> dict:
    """{pcr, ticks} after a JSON round trip: the retained shape (gap 18d)."""
    return json.loads(json.dumps({'pcr': run.pcr, 'ticks': [dataclasses.asdict(t) for t in run.ticks]}, sort_keys=True))


class S3SyntheticSnapshot(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = load_snapshot()
        self.pxc, self.pcr = s3.build_investigation(self.snapshot)

    def test_sys_path_insert_is_intra_repo(self) -> None:
        """The only sys.path insert points inside this repository (CAPTURE.md sys.path rule)."""
        self.assertTrue(REFERENCE.is_dir(), REFERENCE)
        self.assertEqual(Path(SYS_PATH_INSERT).resolve().parents[1], PYTO_ROOT)
        self.assertEqual(Path(s3.__file__).resolve().parent, REFERENCE)

    def test_build_investigation_runs_without_corpus(self) -> None:
        """s3.build_investigation (s3.py:23-91) needs only the snapshot dict; no corpus, no Node bridge."""
        summary = PQL.part('scratch.s3.teeSummary').one(self.pxc)
        self.assertEqual(summary, OBSERVED_SUMMARY)
        self.assertTrue(summary['balanced'])
        # Nothing was written under the reference dir: INV.out_dir (investigation.py:34) is never created.
        self.assertFalse(s3.INV.out_dir.exists(), s3.INV.out_dir)

    def test_check_balance_records_ledger_as_fn_edge(self) -> None:
        """checkBalance testimony inputs == observed mapping; gap 12's {'ledger': 'fn:accountRings'} is its subset."""
        run = self.pcr.run(self.pxc)  # build_investigation discarded its own run (s3.py:90)
        by_id = {c.id: c for t in run.ticks for c in t.calculations}
        self.assertEqual(sorted(by_id), ['accountRings', 'checkBalance'])
        check = by_id['checkBalance']
        self.assertEqual(check.inputs, OBSERVED_CHECK_BALANCE_INPUTS)
        self.assertEqual(check.inputs['ledger'], 'fn:accountRings')
        self.assertEqual(check.calculation, 'fn.quickAnno.s3.checkBalance')
        self.assertEqual(check.into, 'scratch.s3.teeSummary')
        self.assertEqual(check.args, {})

    def test_account_rings_records_only_px_edges(self) -> None:
        """accountRings binds two unwritten Parts, so both inputs are px: (pcr.py:147-149)."""
        run = self.pcr.run(self.pxc)
        account = run.ticks[0].calculations[0]
        self.assertEqual(account.id, 'accountRings')
        self.assertEqual(account.inputs, OBSERVED_ACCOUNT_RINGS_INPUTS)
        self.assertEqual(account.into, 'scratch.s3.ringLedger')

    def test_rerun_matches_retained_testimony(self) -> None:
        """A fresh run's {pcr, ticks} equals testimony.json byte-for-byte after canonical dumps."""
        run = self.pcr.run(self.pxc)
        retained = json.loads(TESTIMONY_PATH.read_text())
        self.assertEqual(testimony_of(run), retained)
        self.assertEqual(
            json.dumps(testimony_of(run), sort_keys=True, indent=2) + '\n',
            TESTIMONY_PATH.read_text(),
        )
        # results are not part of the retained shape (gap 18d) but are checked here for the record
        self.assertEqual(run.results['checkBalance'], OBSERVED_SUMMARY)


if __name__ == '__main__':
    unittest.main()
