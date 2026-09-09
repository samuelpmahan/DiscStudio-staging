"""Day 3 lane C tests: run_cached.py's reuse ledger records outcomes, never asserts them.

The ledger used to write `"outcome": "hit (disk)"` as a string literal for
resolutions 2 and 3 and to multiply the split receipt's duration_ms by a
constant 2 for "two hits", with neither figure derived from `store.counters` or
from the child process's own reported counters. Make every disk load fail the
way a truncated `<key>.json` does (materials.py:236-243 already degrades that to
a miss, honestly) and the old ledger still claimed two hits and non-zero ms
saved -- "dumb receipts and self-verified", origin.md:14-17. These tests pin the
derivation: the ledger must say miss when the resolution missed, and ms saved
must scale with the hits that actually happened.

Run with `python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'`
(check_all.sh discovers this file the same way it discovers every other
`test_*.py` under experiments/grouped-ablation, pyto/scripts/check_all.sh:74).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import materials  # noqa: E402
import run_cached  # noqa: E402

MISSING_CHILD_COUNTERS = {"requests": 1, "hits": 0, "misses": 1, "writes": 1}


def _stored_value(store_root: str | Path):
    """Read the one persisted material value straight off disk.

    Deliberately not through `MaterialsStore.load_value`: these tests patch that
    method to fail, and the stub child below still has to hand `run_cached()` the
    right value or its own value-equality guards (run_cached.py:225-232) would
    raise before the ledger is ever built.
    """
    files = sorted(p for p in Path(store_root).glob("*.json") if not p.name.endswith(".sidecar.json"))
    if len(files) != 1:
        raise AssertionError(f"expected exactly one persisted value file under {store_root}, got {files}")
    return json.loads(files[0].read_text(encoding="utf-8"))


def _child_that_missed(store_root: Path, revision: str) -> dict:
    """Stand-in for `resolve_in_fresh_process` reporting a child that did NOT hit.

    A real child is a separate process, so patching `load_value` in this process
    cannot reach it; this substitutes the report such a child would send back --
    same value, counters that say miss -- which is exactly the input resolution
    3's outcome has to be read from.
    """
    return {
        "materials_root": str(store_root),
        "counters": dict(MISSING_CHILD_COUNTERS),
        "value": _stored_value(store_root),
        "command": ["<stub>", "python3 -I", revision],
        "cwd": str(store_root),
    }


def _raise_load(self, key):  # noqa: ARG001 - signature must match MaterialsStore.load_value
    raise ValueError("simulated truncated <key>.json")


class LedgerOutcomesAreDerivedNotAsserted(unittest.TestCase):
    def setUp(self):
        # A fresh empty root per test: resolution 1 must be a genuine miss, which a
        # root left over from an earlier test (or an earlier run of this suite) would
        # silently turn into a hit.
        self.store_root = tempfile.mkdtemp(prefix="run-cached-test-")
        self.addCleanup(shutil.rmtree, self.store_root, True)

    def test_a_failing_disk_load_makes_the_ledger_say_miss_for_resolutions_2_and_3(self):
        """Kills the mutation `"outcome": outcome_from_delta(delta_b)` ->
        `"outcome": "hit (disk)"` (run_cached.py's resolution-2 row), and the same
        literal on the resolution-3 row: with every load failing, hits never move
        and the ledger must not claim a hit."""
        with mock.patch.object(materials.MaterialsStore, "load_value", _raise_load), \
                mock.patch.object(run_cached, "resolve_in_fresh_process", _child_that_missed):
            report = run_cached.run_cached(store_root=self.store_root)

        ledger = report["reuse_ledger"]
        outcomes = [row["outcome"] for row in ledger["resolutions"]]
        self.assertEqual(outcomes, ["miss+write", "miss+write", "miss+write"], ledger["resolutions"])
        self.assertEqual(report["counters"], {"requests": 2, "hits": 0, "misses": 2, "writes": 2})
        self.assertEqual(ledger["hits_observed"], 0)
        self.assertEqual(ledger["ms_saved_total"], 0)
        self.assertGreater(ledger["ms_saved_per_hit"], 0, "the per-hit figure is still the receipt's duration_ms")
        for row in ledger["resolutions"]:
            self.assertEqual(row["counters_delta"]["hits"], 0, row)

    def test_ms_saved_scales_with_the_hits_that_actually_happened(self):
        """Kills the mutation `round(baseline_ms * hits_observed, 3)` ->
        `round(baseline_ms * 2, 3)`: resolution 2 really hits from disk here and
        resolution 3 really misses, so exactly one hit was observed and the total
        must be one multiple of the per-hit figure, not two."""
        with mock.patch.object(run_cached, "resolve_in_fresh_process", _child_that_missed):
            report = run_cached.run_cached(store_root=self.store_root)

        ledger = report["reuse_ledger"]
        outcomes = [row["outcome"] for row in ledger["resolutions"]]
        self.assertEqual(outcomes, ["miss+write", "hit (disk)", "miss+write"], ledger["resolutions"])
        self.assertEqual(report["counters"], {"requests": 2, "hits": 1, "misses": 1, "writes": 1})
        self.assertEqual(ledger["hits_observed"], 1)
        self.assertEqual(ledger["ms_saved_total"], round(ledger["ms_saved_per_hit"] * 1, 3))
        self.assertEqual(ledger["resolutions"][2]["child_counters"], MISSING_CHILD_COUNTERS)

    def test_interpretation_markdown_reports_the_derived_counts(self):
        """Kills the mutation `f"{ledger['hits_observed']} of ..."` -> a hard-coded
        `"2 of 3"` in interpretation_markdown(): the prose a person reads is the
        artifact the finding is about, so it has to move with the ledger."""
        with mock.patch.object(materials.MaterialsStore, "load_value", _raise_load), \
                mock.patch.object(run_cached, "resolve_in_fresh_process", _child_that_missed):
            report = run_cached.run_cached(store_root=self.store_root)

        markdown = run_cached.interpretation_markdown(report)
        self.assertIn("0 of 3 -> ms saved this run: 0", markdown)
        self.assertNotIn("hit (disk)", markdown)
        self.assertIn("| 2 | in-process, second fresh PxC, same store | miss+write |", markdown)


class OutcomeFromDelta(unittest.TestCase):
    """The mapping itself, without a program run behind it."""

    def test_a_counted_hit_is_the_only_thing_that_reads_as_a_hit(self):
        """Kills the mutation `if hits > 0:` -> `if misses > 0:` in
        outcome_from_delta(): a delta with misses and no hits must not read 'hit'."""
        self.assertEqual(run_cached.outcome_from_delta({"requests": 1, "hits": 1, "misses": 0, "writes": 0}), "hit (disk)")
        self.assertEqual(run_cached.outcome_from_delta({"requests": 1, "hits": 0, "misses": 1, "writes": 1}), "miss+write")
        self.assertEqual(run_cached.outcome_from_delta({"requests": 1, "hits": 0, "misses": 1, "writes": 0}), "miss (no write)")
        self.assertEqual(run_cached.outcome_from_delta({"requests": 0, "hits": 0, "misses": 0, "writes": 0}), "no counter movement")

    def test_counters_delta_subtracts_the_snapshot(self):
        """Kills the mutation `after.get(name, 0) - before.get(name, 0)` ->
        `after.get(name, 0)` in counters_delta(): a shared store's counters
        accumulate, so a raw read would credit resolution 2 with resolution 1's
        movement."""
        before = {"requests": 1, "hits": 0, "misses": 1, "writes": 1}
        after = {"requests": 2, "hits": 1, "misses": 1, "writes": 1}
        self.assertEqual(
            run_cached.counters_delta(before, after),
            {"requests": 1, "hits": 1, "misses": 0, "writes": 0},
        )


class TheLedgerRecordsNoPathThatLandingWouldBreak(unittest.TestCase):
    """`portable()`: the committed ledger must not name this checkout.

    run-6-cached is evidence that gets committed, and it was regenerated from a
    worktree once: `command[0]` and the experiment dir came out as
    `/home/user/.../EXP/0/...`, a receipt pointing at a directory that is deleted
    the moment the pack lands.
    """

    def test_a_path_inside_this_checkout_is_recorded_relative_to_the_root_that_contains_it(self):
        """Kills two one-line mutations in portable(). (1) `return name + "/" +
        Path(os.path.relpath(candidate, root)).as_posix()` -> `return path`: the
        absolute checkout path would be written into the ledger verbatim again.
        (2) That same line back to its pre-fix spelling, `return "<pyto>/" +
        Path(os.path.relpath(candidate, PYTO_ROOT)).as_posix()`: a sibling of
        `pyto/` would be anchored at PYTO_ROOT anyway and come out
        `<pyto>/../.venv/bin/python` -- a placeholder that climbs back out of the
        root it names and resolves to nothing a reader can run.
        """
        inside = str(run_cached.PYTO_ROOT / "experiments" / "grouped-ablation")
        self.assertEqual(run_cached.portable(inside), "<pyto>/experiments/grouped-ablation")
        sibling = str(run_cached.CHECKOUT_ROOT / ".venv" / "bin" / "python")
        self.assertEqual(run_cached.portable(sibling), "<checkout>/.venv/bin/python")
        self.assertEqual(run_cached.portable(str(run_cached.PYTO_ROOT)), "<pyto>")
        self.assertEqual(run_cached.portable(str(run_cached.CHECKOUT_ROOT)), "<checkout>")

    def test_a_symlink_into_this_checkout_is_recorded_by_the_name_that_ran(self):
        """Kills the mutation of the two-candidate loop down to its second half
        (`for candidate in (Path(os.path.realpath(path)),)`).

        This is the case that produced the finding: `command[0]` is
        `sys.executable`, and a venv's `bin/python` is a symlink whose target is
        the system interpreter -- outside the checkout. Resolving first would
        hide exactly the checkout path the ledger is about to write down. Nothing
        is created here; the real interpreter running this suite is the fixture,
        and the test skips when it is not that shape.
        """
        run_by = Path(os.path.normpath(sys.executable))
        if run_cached.CHECKOUT_ROOT not in run_by.parents:
            self.skipTest("this suite is not being run by an interpreter inside the checkout")
        if Path(os.path.realpath(sys.executable)) == run_by:
            self.skipTest("this interpreter is not a symlink, so both candidates coincide")
        recorded = run_cached.portable(sys.executable)
        self.assertTrue(recorded.startswith("<checkout>/"), recorded)
        self.assertNotIn(str(run_cached.CHECKOUT_ROOT), recorded)

    def test_a_path_outside_this_checkout_is_left_exactly_as_it_ran(self):
        """Kills the mutation `if candidate == CHECKOUT_ROOT or CHECKOUT_ROOT in
        candidate.parents:` -> `if True:` in portable(): a system interpreter is
        not ours to rewrite, and `<checkout>/../..` would be a lie about where it
        lives."""
        self.assertEqual(run_cached.portable("/usr/local/bin/python3"), "/usr/local/bin/python3")
        self.assertEqual(run_cached.portable("python3"), "python3")

    def test_the_fresh_process_report_records_the_command_it_will_be_asked_to_publish(self):
        """Kills the mutation `report["command"] = [portable(arg) for arg in args]`
        -> `report["command"] = args` in resolve_in_fresh_process().

        The test above reads the ledger already on disk, which a mutant cannot
        change; this one drives the real child once, because resolution 3's
        `command` row is copied verbatim out of this report and is the field the
        finding was about.
        """
        store_root = tempfile.mkdtemp(prefix="run-cached-child-")
        self.addCleanup(shutil.rmtree, store_root, True)
        try:
            report = run_cached.resolve_in_fresh_process(Path(store_root), "0" * 64)
        except RuntimeError as error:  # the child could not import pyto under `python -I`
            self.skipTest(f"fresh-process resolution is unavailable here: {error}")
        self.assertNotIn(str(run_cached.CHECKOUT_ROOT), json.dumps(report["command"]))
        self.assertEqual(report["command"][5], "<pyto>/experiments/grouped-ablation")

    def test_the_committed_ledger_names_no_directory_that_landing_deletes(self):
        """The finding itself, over the file on disk: whatever regenerated
        evidence/run-6-cached, no absolute path into a checkout may survive in it.
        Kills the same mutations from the other side."""
        ledger_path = os.path.join(HERE, "evidence", "run-6-cached", "reuse-ledger.json")
        text = Path(ledger_path).read_text(encoding="utf-8")
        self.assertNotIn(str(run_cached.CHECKOUT_ROOT), text)
        self.assertNotIn(str(run_cached.PYTO_ROOT), text)
        ledger = json.loads(text)
        command = ledger["resolutions"][2]["command"]
        self.assertEqual(command[5], "<pyto>/experiments/grouped-ablation")


if __name__ == "__main__":
    unittest.main()
