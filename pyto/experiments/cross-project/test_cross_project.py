"""Day 5 tests: the cross-project hit (pyto/questions.md {?} CrossProjectReuse).

Run with `python3 -m unittest discover -s experiments/cross-project -p 'test_*.py'`
(check_all.sh discovers this the same way it discovers every other experiment's
test_*.py -- pyto/scripts/check_all.sh's `for dir in "$PYTO"/experiments/*/` loop,
no separate wiring needed).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pyto import PxC  # noqa: E402

import run  # noqa: E402  -- inserts grouped-ablation onto sys.path as a side effect (its own HERE),
# and imports program/materials itself, so both are importable by name right after this line.
import materials  # noqa: E402  -- grouped-ablation's materials.py
import program  # noqa: E402

PYTHON = sys.executable
STRIPPED_ENV = {"PATH": os.environ.get("PATH", "")}
if os.name == "nt" and os.environ.get("SystemRoot"):
    # See grouped-ablation/run_cached.py and test_run_cached.py: Windows cannot start
    # python.exe from an environment block without SystemRoot; SystemDrive avoids a
    # literal "%SystemDrive%" folder appearing in the child's cwd.
    STRIPPED_ENV["SystemRoot"] = os.environ["SystemRoot"]
    STRIPPED_ENV["SystemDrive"] = os.environ.get("SystemDrive", "C:")


def _fresh_store_root() -> str:
    return tempfile.mkdtemp(prefix="cross-project-test-")


def _ablation_committed_key_and_digest() -> tuple[str, str]:
    path = os.path.join(program.GROUPED_ABLATION, "evidence", "run-6-cached", "reuse-ledger.json")
    with open(path, "r", encoding="utf-8") as fh:
        ledger = json.load(fh)
    return ledger["key"], ledger["split_receipts"]["program_run_1"]["result_sha256"]


class SharedKeyMatchesAblation(unittest.TestCase):
    def test_shared_material_key_equals_ablation_committed_key(self):
        """Kills a mutation to SHARED_SOURCE/SHARED_SEED/SHARED_N in program.py: the
        (revision, source, args) triple must hash to the exact key the ablation
        domain's own committed evidence used for fn.ablation.split on seed 7, n 400."""
        committed_key, _ = _ablation_committed_key_and_digest()
        args = program.shared_split_args()
        key = materials.material_key(revision=program.SHARED_REVISION, source=program.SHARED_SOURCE, args=args)
        self.assertEqual(key, committed_key)


class SeedingAndHitting(unittest.TestCase):
    def setUp(self):
        # Isolates the store with PYTO_MATERIALS_DIR in a temp dir, mirroring
        # test_run_cached.py's isolation; run_cross_project is also given the same
        # root explicitly (belt and suspenders -- materials.default_root() reads the
        # env var at call time, and every call below passes store_root explicitly).
        self.store_root = _fresh_store_root()
        os.environ["PYTO_MATERIALS_DIR"] = self.store_root
        self.addCleanup(os.environ.pop, "PYTO_MATERIALS_DIR", None)
        self.addCleanup(shutil.rmtree, self.store_root, True)

    def test_empty_store_is_seeded_by_domain_a_then_hits(self):
        """On a genuinely empty store, Step A must produce the ablation material
        itself (seeded_by_domain_a True) before Step B's dedicated resolution can be
        a hit."""
        report = run.run_cross_project(store_root=self.store_root)
        ledger = report["ledger"]
        self.assertTrue(ledger["shared_material"]["seeded_by_domain_a"])
        self.assertEqual(ledger["resolutions"][0]["material"], "fn.ablation.split (shared)")
        self.assertGreaterEqual(ledger["resolutions"][0]["counters_delta"]["hits"], 1)

    def test_prepopulated_store_gives_one_hit_and_misses_for_shelf_calcs_before_any_write(self):
        """Pre-seed only the ablation material (as run_cached.py, or a prior domain-A
        run, would have); the shelf's own two Calculations must then be misses on
        their first resolution, and the split resolution's hit must be recorded with
        zero writes before either shelf miss writes anything."""
        args = program.shared_split_args()
        materials.material(
            PxC(), revision=program.SHARED_REVISION, source=program.SHARED_SOURCE,
            calculation=program.SHARED_CALCULATION, args=args,
            store=materials.MaterialsStore(root=self.store_root),
        )
        report = run.run_cross_project(store_root=self.store_root)
        ledger = report["ledger"]
        self.assertFalse(ledger["shared_material"]["seeded_by_domain_a"])
        by_material = {row["material"]: row["counters_delta"] for row in ledger["resolutions"]}
        self.assertEqual(by_material["fn.ablation.split (shared)"]["hits"], 1)
        self.assertEqual(by_material["fn.ablation.split (shared)"]["writes"], 0)
        self.assertEqual(by_material["fn.shelf.stabilityHistogram (own)"]["misses"], 1)
        self.assertEqual(by_material["fn.shelf.pickToCarry (own)"]["misses"], 1)
        self.assertGreaterEqual(ledger["hits_before_any_shelf_write"], 1)
        self.assertEqual(ledger["writes_before_any_shelf_write"], 0)


class DigestVerification(unittest.TestCase):
    def test_shared_hit_digest_matches_ablation_committed_evidence(self):
        """Step C's whole point: the value read back through the shared store must
        digest to exactly what the ablation experiment committed, cited from two
        independent files (run-6-cached and run-1's own receipts)."""
        store_root = _fresh_store_root()
        self.addCleanup(shutil.rmtree, store_root, True)
        report = run.run_cross_project(store_root=store_root)
        shared = report["ledger"]["shared_material"]
        self.assertTrue(shared["digest_equal"])
        _, committed_digest = _ablation_committed_key_and_digest()
        self.assertEqual(shared["digest_this_run"], committed_digest)
        # cross-checked against the second citation directly, not only via run.py's own logic
        receipts_path = os.path.join(program.GROUPED_ABLATION, "evidence", "run-1", "receipts.json")
        with open(receipts_path, "r", encoding="utf-8") as fh:
            receipts = json.load(fh)
        self.assertEqual(shared["digest_this_run"], receipts["split"]["result_sha256"])


class FreshChildProcess(unittest.TestCase):
    def test_second_run_in_fresh_child_process_hits_everything(self):
        """A genuinely fresh `python3 -I` process, told only PYTO_MATERIALS_DIR (env
        stripped to PATH/SystemRoot/SystemDrive, the same pattern run_cached.py's
        subprocess uses), re-resolves all three materials as hits -- the store, not
        this process, is what makes it a cross-project hit."""
        store_root = _fresh_store_root()
        self.addCleanup(shutil.rmtree, store_root, True)
        run.run_cross_project(store_root=store_root)  # populate: split (seed+hit), histogram, carry

        snippet = textwrap.dedent(
            f"""\
            import json, sys
            sys.path.insert(0, {HERE!r})
            import run
            report = run.run_cross_project(store_root={store_root!r})
            print(json.dumps(report["ledger"]["resolutions"]))
            """
        )
        env = dict(STRIPPED_ENV)
        env["PYTO_MATERIALS_DIR"] = store_root
        completed = subprocess.run([PYTHON, "-I", "-B", "-c", snippet], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        resolutions = json.loads(completed.stdout)
        for row in resolutions:
            self.assertGreaterEqual(row["counters_delta"]["hits"], 1, row)
            self.assertEqual(row["counters_delta"]["misses"], 0, row)


class RevisionChangeIsAMiss(unittest.TestCase):
    def test_changing_a_shelf_revision_string_is_a_miss_not_a_hit(self):
        """program.HISTOGRAM_REVISION, mutated, must produce a DIFFERENT key and
        therefore a miss on a store that already holds the original -- the caller-
        supplies-the-revision design materials.py documents (materials.py:48-55)."""
        store_root = _fresh_store_root()
        self.addCleanup(shutil.rmtree, store_root, True)
        store = materials.MaterialsStore(root=store_root)
        bag = program.make_bag(1, 12)
        source = {"domain": "shelf", "bag_seed": 1, "bag_n": 12}

        original_key = materials.material_key(revision=program.HISTOGRAM_REVISION, source=source, args={"bag": bag})
        materials.material(
            PxC(), revision=program.HISTOGRAM_REVISION, source=source,
            calculation=program.REGISTRY["fn.shelf.stabilityHistogram"], args={"bag": bag}, store=store,
        )
        self.assertTrue(store.has_value(original_key))

        mutated_revision = program.HISTOGRAM_REVISION + "-mutated"
        mutated_key = materials.material_key(revision=mutated_revision, source=source, args={"bag": bag})
        self.assertNotEqual(mutated_key, original_key)

        before = dict(store.counters)
        materials.material(
            PxC(), revision=mutated_revision, source=source,
            calculation=program.REGISTRY["fn.shelf.stabilityHistogram"], args={"bag": bag}, store=store,
        )
        self.assertEqual(store.counters["misses"], before.get("misses", 0) + 1)
        self.assertEqual(store.counters["hits"], before.get("hits", 0))


class RefusesOverwrite(unittest.TestCase):
    def test_refuses_to_overwrite_existing_out_dir_without_force(self):
        out_dir = tempfile.mkdtemp(prefix="cross-project-out-")
        self.addCleanup(shutil.rmtree, out_dir, True)
        with open(os.path.join(out_dir, "counters.json"), "w", encoding="utf-8") as fh:
            fh.write("{}")
        with self.assertRaises(FileExistsError):
            run.resolve_out_dir(out_dir, force=False)
        self.assertEqual(run.resolve_out_dir(out_dir, force=True), out_dir)


class NoCodeCopied(unittest.TestCase):
    def test_no_ablation_files_duplicated_into_cross_project(self):
        """This experiment must not carry its own calculations.py/features.py/
        run_cached.py/materials.py -- the deliverable's 'do not copy code' rule; it
        imports grouped-ablation's instead (program.py's own module docstring)."""
        for name in ("calculations.py", "features.py", "run_cached.py", "materials.py"):
            self.assertFalse(os.path.exists(os.path.join(HERE, name)), name)


class CommittedEvidenceIsPortable(unittest.TestCase):
    def test_committed_run1_evidence_has_no_absolute_checkout_paths(self):
        evidence_dir = os.path.join(HERE, "evidence", "run-1")
        if not os.path.isdir(evidence_dir):
            self.skipTest("evidence/run-1 not present in this checkout")
        checkout_root = os.path.normpath(os.path.join(HERE, "..", "..", "..")).replace(os.sep, "/")
        for name in os.listdir(evidence_dir):
            text = Path(evidence_dir, name).read_text(encoding="utf-8").replace(os.sep, "/")
            self.assertNotIn(checkout_root, text, name)


if __name__ == "__main__":
    unittest.main()
