"""Day 3 lane C tests: materials.py's content-addressed store and hits.py's ledger.

Run with `python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'`
(check_all.sh discovers this file the same way it discovers every other
`test_*.py` under experiments/grouped-ablation -- no separate wiring needed).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SRC_PYTO = os.path.join(REPO, "pyto", "src", "pyto")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pyto import PxC  # noqa: E402
from pyto.pcr import PcrRun  # noqa: E402

import materials  # noqa: E402
from calculations import REGISTRY, split  # noqa: E402
from features import make_data  # noqa: E402
from hits import hit_ledger  # noqa: E402
from run import run_experiment  # noqa: E402

PYTHON = sys.executable
STRIPPED_ENV = {"PATH": os.environ.get("PATH", "")}
if os.name == "nt" and os.environ.get("SystemRoot"):
    # See replay.py: Windows hands the child exactly this block and nothing else, and python.exe
    # will not start without SystemRoot in it (CPython skips its own
    # test_subprocess.py::test_empty_env on win32 for this reason). It is the one
    # variable the strip keeps, and only there.
    STRIPPED_ENV["SystemRoot"] = os.environ["SystemRoot"]
    STRIPPED_ENV["SystemDrive"] = os.environ.get("SystemDrive", "C:")  # else a literal "%SystemDrive%" folder appears in cwd


def _fresh_store(root: str | None = None) -> materials.MaterialsStore:
    return materials.MaterialsStore(root=root or tempfile.mkdtemp(prefix="materials-test-"))


class CanonicalAndKeyStability(unittest.TestCase):
    def test_canonical_is_independent_of_dict_insertion_order(self):
        a = {"revision": "r1", "source": {"seed": 7, "n": 400}, "args": {"z": 1, "a": 2}}
        b = {"args": {"a": 2, "z": 1}, "source": {"n": 400, "seed": 7}, "revision": "r1"}
        self.assertEqual(materials.canonical(a), materials.canonical(b))
        self.assertEqual(materials.sha(materials.canonical(a)), materials.sha(materials.canonical(b)))

    def test_key_is_independent_of_nested_dict_order(self):
        key_a = materials.material_key(revision="r1", source={"x": 1, "y": 2}, args={"b": 2, "a": 1})
        key_b = materials.material_key(revision="r1", source={"y": 2, "x": 1}, args={"a": 1, "b": 2})
        self.assertEqual(key_a, key_b)

    def test_different_revision_gives_a_different_key(self):
        key_a = materials.material_key(revision="rev-A", source={"seed": 7}, args={"rows": [1, 2, 3]})
        key_b = materials.material_key(revision="rev-B", source={"seed": 7}, args={"rows": [1, 2, 3]})
        self.assertNotEqual(key_a, key_b)

    def test_different_args_gives_a_different_key_even_with_same_revision_and_source(self):
        key_a = materials.material_key(revision="rev-A", source={"seed": 7}, args={"rows": [1, 2]})
        key_b = materials.material_key(revision="rev-A", source={"seed": 7}, args={"rows": [1, 3]})
        self.assertNotEqual(key_a, key_b)

    def test_key_is_stable_across_a_fresh_process(self):
        """The same canonical()/sha() computed in this process and in a genuinely fresh
        `python3 -I` process (no shared Python object identity, no cached bytecode)
        agree bit for bit -- the key is a pure function of its inputs, not of anything
        process-local (pcr.py's own `_result_sha256` docstring names exactly this
        failure mode for a digest that leaks process state)."""
        payload = {"revision": "rev-A", "source": {"seed": 7, "n": 400}, "args": {"rows": [[1, 2], 3.5]}}
        expected = materials.material_key(**payload)
        snippet = textwrap.dedent(
            f"""\
            import sys
            sys.path.insert(0, {HERE!r})
            import materials
            print(materials.material_key(**{payload!r}))
            """
        )
        completed = subprocess.run(
            [PYTHON, "-I", "-B", "-c", snippet], env=dict(STRIPPED_ENV), capture_output=True, text=True, timeout=30
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), expected)


class MaterialHitsAndMisses(unittest.TestCase):
    def test_first_run_misses_second_run_hits_with_a_fresh_pxc(self):
        store = _fresh_store()
        rows = make_data(7, 20)
        args = {"rows": rows}

        pxc_a = PxC()
        value_a = materials.material(
            pxc_a, revision="rev-1", source={"seed": 7, "n": 20},
            calculation=REGISTRY["fn.ablation.split"], args=args, store=store,
        )
        self.assertEqual(store.counters, {"requests": 1, "hits": 0, "misses": 1, "writes": 1})

        pxc_b = PxC()  # fresh: never saw the material.<key> address before
        value_b = materials.material(
            pxc_b, revision="rev-1", source={"seed": 7, "n": 20},
            calculation=REGISTRY["fn.ablation.split"], args=args, store=store,
        )
        self.assertEqual(store.counters, {"requests": 2, "hits": 1, "misses": 1, "writes": 1})
        self.assertEqual(value_a, value_b)

    def test_pxc_hit_does_not_touch_the_store_counters_beyond_requests_and_hits(self):
        """Asking the SAME pxc twice: the second ask is a PxC hit, never a disk read."""
        store = _fresh_store()
        pxc = PxC()
        args = {"rows": make_data(7, 20)}
        materials.material(pxc, revision="rev-1", source={"n": 20}, calculation=REGISTRY["fn.ablation.split"], args=args, store=store)
        counters_after_first = dict(store.counters)
        materials.material(pxc, revision="rev-1", source={"n": 20}, calculation=REGISTRY["fn.ablation.split"], args=args, store=store)
        self.assertEqual(store.counters["requests"], counters_after_first["requests"] + 1)
        self.assertEqual(store.counters["hits"], counters_after_first["hits"] + 1)
        self.assertEqual(store.counters["misses"], counters_after_first["misses"])
        self.assertEqual(store.counters["writes"], counters_after_first["writes"])

    def test_a_calculation_that_would_raise_is_never_called_on_a_hit(self):
        """Proof that a hit really skips the Calculation: the second resolution's
        Calculation raises if invoked at all."""
        store = _fresh_store()
        calls = {"n": 0}

        def _boom(args):
            calls["n"] += 1
            raise AssertionError("material() called the Calculation on what should have been a hit")

        from pyto import Calculation
        real = Calculation("fn.ablation.split", split)
        boom = Calculation("fn.ablation.split", _boom)
        args = {"rows": make_data(7, 20)}

        pxc_a = PxC()
        materials.material(pxc_a, revision="rev-1", source={"n": 20}, calculation=real, args=args, store=store)

        pxc_b = PxC()  # fresh PxC, disk already holds the value -> must not call `boom`
        value = materials.material(pxc_b, revision="rev-1", source={"n": 20}, calculation=boom, args=args, store=store)
        self.assertEqual(calls["n"], 0)
        self.assertEqual(value, split(args))


class DiskHitAcrossAFreshProcess(unittest.TestCase):
    def test_disk_hit_survives_a_fresh_python_dash_i_process(self):
        """Write a value from THIS process; a genuinely fresh `python3 -I` process,
        told only PYTO_MATERIALS_DIR, resolves the same key as a hit without ever
        calling the Calculation (the child's own Calculation raises if called)."""
        store_root = tempfile.mkdtemp(prefix="materials-crossproc-")
        store = materials.MaterialsStore(root=store_root)
        args = {"rows": make_data(7, 20)}
        materials.material(store=store, pxc=PxC(), revision="rev-x", source={"n": 20}, calculation=REGISTRY["fn.ablation.split"], args=args)

        snippet = textwrap.dedent(
            f"""\
            import json, sys
            sys.path.insert(0, {HERE!r})
            import materials
            from pyto import PxC

            def boom(args):
                raise AssertionError("the child recomputed instead of hitting the disk store")

            from pyto import Calculation
            store = materials.MaterialsStore()  # PYTO_MATERIALS_DIR from the parent's env
            value = materials.material(
                PxC(), revision="rev-x", source={{"n": 20}}, args={args!r},
                calculation=Calculation("fn.ablation.split", boom), store=store,
            )
            print(json.dumps({{"counters": store.counters, "value": value}}))
            """
        )
        env = dict(STRIPPED_ENV)
        env["PYTO_MATERIALS_DIR"] = store_root
        completed = subprocess.run([PYTHON, "-I", "-B", "-c", snippet], env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["counters"], {"requests": 1, "hits": 1, "misses": 0, "writes": 0})
        self.assertEqual(report["value"], split(args))


class NonJSONValueSidecar(unittest.TestCase):
    """A Calculation returning a non-JSON-serializable value (a Python set here, chosen
    because repr({1,2,3}) is deterministic: CPython does not randomize small-int hashes
    regardless of PYTHONHASHSEED, unlike str)."""

    ADDRESS = "fn.materials-test.nonjson"

    @staticmethod
    def _make_set(args):
        return {1, 2, 3}

    def test_non_json_value_is_written_to_a_sidecar_not_a_value_file(self):
        from pyto import Calculation
        calc = Calculation(self.ADDRESS, self._make_set)
        store = _fresh_store()
        value = materials.material(PxC(), revision="r1", source={}, calculation=calc, args={}, store=store)
        self.assertEqual(value, {1, 2, 3})
        key = materials.material_key(revision="r1", source={}, args={})
        self.assertFalse(store.has_value(key), "a non-JSON value must not be persisted as a loadable value")
        self.assertTrue((store.root / f"{key}.sidecar.json").is_file())
        sidecar = json.loads((store.root / f"{key}.sidecar.json").read_text(encoding="utf-8"))
        self.assertEqual(set(sidecar), {"digest", "ref", "type"})
        self.assertEqual(sidecar["type"], "set")
        self.assertTrue((store.root / sidecar["ref"]).is_file())

    def test_non_json_value_is_not_treated_as_a_hit_on_reload(self):
        from pyto import Calculation
        calls = {"n": 0}

        def counting_calc(args):
            calls["n"] += 1
            return {1, 2, 3}

        calc = Calculation(self.ADDRESS, counting_calc)
        store = _fresh_store()

        materials.material(PxC(), revision="r1", source={}, calculation=calc, args={}, store=store)
        self.assertEqual(calls["n"], 1)
        self.assertEqual(store.counters["misses"], 1)
        self.assertEqual(store.counters["hits"], 0)

        # A second, fresh PxC over the SAME store: since the value was never actually
        # persisted (only its digest+ref sidecar was), this must recompute -- a second
        # miss, not a hit -- rather than silently pretending the sidecar is the value.
        materials.material(PxC(), revision="r1", source={}, calculation=calc, args={}, store=store)
        self.assertEqual(calls["n"], 2)
        self.assertEqual(store.counters, {"requests": 2, "hits": 0, "misses": 2, "writes": 2})


class CorruptValueFileIsNotAHit(unittest.TestCase):
    """A value file that will not read back is a miss, not a half-counted hit.

    `material()` used to increment `hits` before `load_value()` ran, so a truncated
    or hand-edited `<key>.json` recorded a hit and *then* raised: a ledger claiming
    reuse of a value nobody ever read, in which hits + misses no longer accounted
    for requests. The rule the module states for a sidecar-only key -- recompute
    rather than silently pretend to be cached -- applies here too.
    """

    ADDRESS = "fn.materials-test.corrupt"

    def _run(self, store, calc, pxc=None):
        return materials.material(
            pxc or PxC(), revision="r1", source={"n": 3}, calculation=calc, args={}, store=store
        )

    def test_a_truncated_value_file_recomputes_and_counts_a_miss(self):
        from pyto import Calculation
        calls = {"n": 0}

        def counting_calc(args):
            calls["n"] += 1
            return {"n": 3}

        calc = Calculation(self.ADDRESS, counting_calc)
        store = _fresh_store()
        self.assertEqual(self._run(store, calc), {"n": 3})
        self.assertEqual(store.counters, {"requests": 1, "hits": 0, "misses": 1, "writes": 1})

        key = materials.material_key(revision="r1", source={"n": 3}, args={})
        value_file = store.root / f"{key}.json"
        self.assertTrue(value_file.is_file())
        value_file.write_text('{"n": 3', encoding="utf-8")  # truncated mid-object

        # No exception escapes, the Calculation runs again, and the ledger says so.
        self.assertEqual(self._run(store, calc), {"n": 3})
        self.assertEqual(calls["n"], 2)
        self.assertEqual(store.counters, {"requests": 2, "hits": 0, "misses": 2, "writes": 2})
        self.assertEqual(
            store.counters["hits"] + store.counters["misses"], store.counters["requests"],
            "hits + misses must still account for every request",
        )
        # The miss path rewrote the file, so the next ask is an honest disk hit.
        self.assertEqual(self._run(store, calc), {"n": 3})
        self.assertEqual(calls["n"], 2)
        self.assertEqual(store.counters, {"requests": 3, "hits": 1, "misses": 2, "writes": 2})

    def test_a_stored_null_is_still_a_hit(self):
        """The sentinel for a failed load is not None: `null` is a legal cached value."""
        from pyto import Calculation
        calls = {"n": 0}

        def none_calc(args):
            calls["n"] += 1
            return None

        calc = Calculation(self.ADDRESS, none_calc)
        store = _fresh_store()
        self.assertIsNone(self._run(store, calc))
        self.assertIsNone(self._run(store, calc))  # fresh PxC, disk hit
        self.assertEqual(calls["n"], 1, "a stored null must not be recomputed")
        self.assertEqual(store.counters, {"requests": 2, "hits": 1, "misses": 1, "writes": 1})


class HitLedger(unittest.TestCase):
    def test_calculation_hits_and_part_hits_on_the_day1_program(self):
        """15 invocations: select, split, 6x(fit,score), compare. `select` and `split`
        each read one external ('preexisting') Part -> 2 part hits. `fn.ablation.fit`
        and `fn.ablation.score` are each invoked six times (once per variant: baseline
        + 5 drop_* ablations) sharing one Calculation address each -> the first
        invocation of each registers it, the other five are hits -> 10 calculation
        hits. `select`, `split` and `compare` each have a unique address -> 0 hits
        from them."""
        result = run_experiment(7, 400)
        ledger = hit_ledger(result["run"])
        self.assertEqual(ledger["counters"], {"invocations": 15, "part_hits": 2, "calculation_hits": 10})
        self.assertEqual({row["address"] for row in ledger["part_hits"]}, {"input.ablation.rows", "input.ablation.groups"})
        self.assertEqual({row["calculation"] for row in ledger["calculation_hits"]}, {"fn.ablation.fit", "fn.ablation.score"})
        self.assertTrue(all(row["invocation_id"] for row in ledger["calculation_hits"]))

    def test_hit_ledger_on_a_run_record_dict_matches_the_pcrrun_form(self):
        """RECORD.md's px:-prefixed declared_consumes spelling round-trips to the same
        counts as the PcrRun form (materialize.py already emits px:-prefixed spellings,
        pyto/src/pyto/materialize.py:328-330)."""
        from pyto.materialize import run_record

        result = run_experiment(7, 400)
        record = run_record(result["run"], result["pxc"])
        from_run = hit_ledger(result["run"])
        from_record = hit_ledger(record)
        self.assertEqual(from_run["counters"], from_record["counters"])

    def test_empty_receipts_gives_zero_counts_rather_than_guessing(self):
        result = run_experiment(7, 400)
        empty_run = PcrRun(result["run"].pcr, result["run"].ticks, result["run"].results, {})
        ledger = hit_ledger(empty_run)
        self.assertEqual(ledger["counters"], {"invocations": 0, "part_hits": 0, "calculation_hits": 0})

    def test_rejects_an_unrecognized_input_type(self):
        with self.assertRaises(TypeError):
            hit_ledger(["not", "a", "record"])


class LibraryUntouched(unittest.TestCase):
    def test_no_new_module_under_pyto_src(self):
        self.assertFalse(os.path.exists(os.path.join(SRC_PYTO, "materials.py")))
        self.assertFalse(os.path.exists(os.path.join(SRC_PYTO, "hits.py")))

    def test_git_status_is_clean_under_pyto_src(self):
        completed = subprocess.run(
            ["git", "status", "--porcelain", "--", "pyto/src"],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "", f"pyto/src is not clean:\n{completed.stdout}")


if __name__ == "__main__":
    unittest.main()
