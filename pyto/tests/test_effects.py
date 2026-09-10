"""Executable spec of `oc`, the Effects handle and replay from the record (task 49).

Lane 1's statement: "Two kinds of Calculation and no third: `fn` is pure; `oc`
(OperationalCalculation) is the syscall table, the only place an effect happens
(shell, file, git, network), and it records what it read and what it produced as
Parts so replay plays the Part back instead of re-running the effect." The
owner's framing: the receipt is the subject, and an OS with no effects is a
calculator.

The oracle every test here turns on: **an effect that is not on the receipt did
not happen**. Concretely --

* an `oc` performs its effects only through the handle `PCR.run` gives it, and
  every call lands in that invocation's ledger, on its Receipt and in the record;
* an `fn` is called with no handle at all, so purity is a missing key rather than
  a promise;
* a replay fed that ledger reproduces the receipt byte for byte in a fresh
  process -- the clock, the seed and the draws come back out of the record, the
  file is written again and re-digested -- and refuses the moment the record and
  the program disagree, naming the invocation, the kind and the index.

Mutation-checked claims (one-line edits applied to a scratch copy of the tree,
never to the repository; see pyto/experiments/tasks/49/packet.md):

    core.py:Calculation.__post_init__ refuses any root but      -> `startswith("")`
        `fn.`/`oc.` (`startswith(CALCULATION_ROOTS)`)
        and PurityIsAMissingHandle.test_the_two_roots_and_no_third fails: killed.
    pcr.py:_prepare passes the handle only to an `oc.`          -> `if True:`
        Calculation (`if invocation.calculation.is_operational`)
        and PurityIsAMissingHandle.test_a_pure_calculation_gets_no_handle fails
        (the fn reads args["effects"] and no KeyError is raised): killed.
    effects.py:ReplayEffects._next checks the recorded result   -> `if False:`
        against its own digest before feeding it back
        and Tampering.test_a_tampered_effect_digest_is_refused_naming_the_-
        invocation_and_index fails (the child replays the tampered ledger and
        exits 0): killed.

All three were run against a scratch copy of the tree on 2026-09-10 and each
killed the named test and no other.
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
import tempfile
import unittest

from pyto import PCR, Calculation, Part, PxC
from pyto.effects import EFFECT_KINDS, EffectRefused, Effects, ReplayEffects, effect_digest
from pyto.materialize import run_record

PYTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(PYTO_ROOT, "src")
TESTS = os.path.dirname(os.path.abspath(__file__))

# The second reader of the shared format, as tests/test_materialize.py loads it:
# a validator transcribed from RECORD.md independently of the producer.
VIEWER_TEST_DIR = os.path.join(PYTO_ROOT, "viewer", "test")
if VIEWER_TEST_DIR not in sys.path:
    print(f"[tests/test_effects] sys.path.insert(0, {VIEWER_TEST_DIR!r})", file=sys.stderr)
    sys.path.insert(0, VIEWER_TEST_DIR)

from record_schema import RecordSchemaError  # noqa: E402
from record_schema import validate as validate_record  # noqa: E402

if TESTS not in sys.path:
    print(f"[tests/test_effects] sys.path.insert(0, {TESTS!r})", file=sys.stderr)
    sys.path.insert(0, TESTS)

import fixture_effects  # noqa: E402  -- the oc program this whole file turns on
from fixture_effects import (  # noqa: E402
    NOTE_PATH,
    NOTE_TEXT,
    STAMP,
    build_program,
    comparable_receipts,
    ledgers_from_record,
)

EXPECTED_KINDS = ("write_text", "now_ms", "random_seed", "random", "random")
"""The five effects of `oc.effects.stamp`, in the order it makes them.

Five and not four: `random(1)` twice draws twice, and the first of them records
the seed it drew, because the seed comes from outside the program and a replay
that re-seeded itself would not be a replay.
"""


def run_once(root: str, *, observe: bool = True, note: str = NOTE_TEXT):
    """The fixture program, run against a fresh store with `root` as its world."""
    pcr = build_program(note)
    pxc = PxC()
    return pcr, pxc, pcr.run(pxc, observe=observe, effects_root=root)


def record_of(pcr, pxc, run) -> dict:
    return run_record(run, pxc, preexisting=set())


# --- the fresh-process replay child -------------------------------------------

CHILD = r"""
import json
import sys

src, tests_dir, record_path, root = sys.argv[1:5]
# One explicit, logged sys.path insert per directory (experiments/CAPTURE.md):
# the package under test and the fixture program the record describes.
for entry in (src, tests_dir):
    print("[replay-child] sys.path.insert(0, %r)" % entry, file=sys.stderr)
    sys.path.insert(0, entry)

import fixture_effects
from pyto import PxC

with open(record_path, encoding="utf-8") as handle:
    record = json.load(handle)

pcr = fixture_effects.build_program()
pxc = PxC()
run = pcr.run(
    pxc,
    observe=True,
    effects_root=root,
    replay_effects=fixture_effects.ledgers_from_record(record),
)
print(fixture_effects.comparable_receipts(run))
"""


def replay_in_a_fresh_process(record_path: str, root: str) -> subprocess.CompletedProcess:
    """`python -I -c <child>` with a stripped environment and a cwd outside the repo.

    The shape `experiments/students/grade.py` check 2 uses, for the same reason:
    a replay that needs this process's environment, this process's cwd or this
    process's already-imported modules is not a replay.
    """
    with tempfile.TemporaryDirectory() as elsewhere:
        return subprocess.run(
            [sys.executable, "-I", "-c", CHILD, SRC, TESTS, record_path, root],
            capture_output=True,
            text=True,
            cwd=elsewhere,
            env={"PATH": os.environ.get("PATH", "")},
        )


class TheLedger(unittest.TestCase):
    """What one `oc` invocation records, and what an `fn` records (nothing)."""

    def test_five_effects_with_digests_on_the_receipt(self):
        """effects.py + pcr.py: every call appends one entry, in order, with a digest.

        The claim the whole task rests on: the receipt is the subject. A write, a
        clock reading, a seed and two draws are five entries -- not four, because
        the seed is an effect -- and each carries the sha256 of its recorded
        value.
        """
        with tempfile.TemporaryDirectory() as root:
            _, _, run = run_once(root)
            receipt = run.receipts["stamp"]
            self.assertEqual(tuple(effect.kind for effect in receipt.effects), EXPECTED_KINDS)
            self.assertEqual(len(receipt.effects), 5)
            for effect in receipt.effects:
                self.assertIn(effect.kind, EFFECT_KINDS)
                self.assertRegex(effect.result_sha256, r"^[0-9a-f]{64}$")
            # The write's digest is the digest of the text, and the file is there.
            self.assertEqual(receipt.effects[0].args, {"path": NOTE_PATH})
            self.assertIsNone(receipt.effects[0].result)
            self.assertEqual(receipt.effects[0].result_sha256, effect_digest(NOTE_TEXT))
            with open(os.path.join(root, "out", "note.txt"), encoding="utf-8") as handle:
                self.assertEqual(handle.read(), NOTE_TEXT)
            # The seed is recorded, and the draws are the draws of that seed.
            self.assertEqual(receipt.effects[2].kind, "random_seed")
            self.assertIsInstance(receipt.effects[2].result, int)
            self.assertEqual(run.results["stamp"]["draws"][0], receipt.effects[3].result[0])

    def test_a_pure_invocation_has_an_empty_ledger(self):
        """`fn.effects.summarize` performed no effect, and its receipt says so."""
        with tempfile.TemporaryDirectory() as root:
            _, _, run = run_once(root)
            self.assertEqual(run.receipts["summary"].effects, ())
            self.assertEqual(sorted(run.effects), ["stamp"])

    def test_paths_are_relative_to_the_root_and_an_escape_is_refused(self):
        """effects.py:_Handle._relative -- a ledger replays somewhere else or it lies."""
        with tempfile.TemporaryDirectory() as root:
            handle = Effects(root)
            handle.write_text("a/b/c.txt", "x")
            self.assertEqual(handle.ledger[0].args["path"], "a/b/c.txt")
            self.assertNotIn(root, json.dumps(handle.entries()))
            with self.assertRaisesRegex(ValueError, "escapes the effects_root"):
                handle.write_text("../outside.txt", "x")
            with self.assertRaisesRegex(ValueError, "escapes the effects_root"):
                handle.read_text(os.path.join(os.path.dirname(root), "outside.txt"))

    def test_the_same_ledger_replays_the_same_way_twice(self):
        """effects.py: ReplayEffects is a pure function of the ledger it was given."""
        with tempfile.TemporaryDirectory() as root:
            live = Effects(root, seed_source=11)
            live.write_text(NOTE_PATH, NOTE_TEXT)
            live.now_ms()
            live.random(2)
            live.env("PATH")
            recorded = live.entries()
            answers = []
            for _ in range(2):
                with tempfile.TemporaryDirectory() as elsewhere:
                    replay = ReplayEffects(recorded, elsewhere)
                    replay.write_text(NOTE_PATH, NOTE_TEXT)
                    answers.append((replay.now_ms(), replay.random(2), replay.env("PATH")))
                    self.assertEqual(replay.entries(), recorded)
                    self.assertEqual(replay.remaining(), ())
            self.assertEqual(answers[0], answers[1])


class TheRecord(unittest.TestCase):
    """`effects` in the run record, and the validator that was written from RECORD.md."""

    def test_the_record_carries_the_ledger_and_validates(self):
        """materialize.py + record_schema.py: present for every invocation, empty for fn.

        Mutation: materialize.py `run_record`, drop `effects` from the invocation
        dict -- this fails at the first assertion, and the replay tests fail with
        it, because the record is where a replay gets the ledger.
        """
        with tempfile.TemporaryDirectory() as root:
            pcr, pxc, run = run_once(root)
            record = validate_record(record_of(pcr, pxc, run))
            by_id = {
                inv["id"]: inv for tick in record["ticks"] for inv in tick["invocations"]
            }
            self.assertEqual(len(by_id["stamp"]["effects"]), 5)
            self.assertEqual(by_id["summary"]["effects"], [])
            entry = by_id["stamp"]["effects"][0]
            self.assertEqual(sorted(entry), ["args", "kind", "result", "result_sha256"])
            self.assertEqual(entry["args"]["path"], NOTE_PATH)
            self.assertIsNone(entry["result"])

    def test_a_pure_run_carries_no_effects_field_at_all(self):
        """The `{?} EffectsFieldOptional` bargain: a pure record is the record it was.

        Absent means "this run performed none", which is what every runtime that
        never heard of an `oc.` writes -- and it is what keeps every committed
        record (and every consumer that compares one byte for byte) working.
        """
        double = Calculation("fn.effects.double", lambda args: args["value"] * 2)
        pcr = PCR("pure")
        pcr.calc("T", double, id="d", into=Part("scratch.pure.out"), args={"value": 2})
        pxc = PxC()
        run = pcr.run(pxc, observe=True)
        record = validate_record(run_record(run, pxc, preexisting=set()))
        self.assertNotIn("effects", record["ticks"][0]["invocations"][0])

    def test_the_validator_refuses_an_effect_the_format_does_not_declare(self):
        """record_schema.py:_effects -- unknown kind, unknown field, absolute path."""
        with tempfile.TemporaryDirectory() as root:
            pcr, pxc, run = run_once(root)
            record = record_of(pcr, pxc, run)
            effects = record["ticks"][0]["invocations"][0]["effects"]

            for mutate, path in (
                (lambda: effects[0].__setitem__("kind", "spawn"), "effects[0].kind"),
                (lambda: effects[0].__setitem__("nonce", 1), "effects[0]"),
                (lambda: effects[0]["args"].__setitem__("path", "/etc/passwd"), "effects[0].args.path"),
                (lambda: effects[0]["args"].__setitem__("path", "../out.txt"), "effects[0].args.path"),
                (lambda: effects[0].__setitem__("result", "the text"), "effects[0].result"),
            ):
                original = json.loads(json.dumps(effects[0]))
                mutate()
                with self.assertRaises(RecordSchemaError) as caught:
                    validate_record(record)
                self.assertIn(path, caught.exception.path)
                effects[0].clear()
                effects[0].update(original)
            validate_record(record)


class FreshProcessReplay(unittest.TestCase):
    """The claim: the record replays in a process that shares nothing with this one."""

    def test_replay_reproduces_the_receipt_byte_for_byte(self):
        """pcr.py + effects.py: the clock, the seed and the draws come out of the record.

        `-I`, a stripped environment and a cwd outside the repository, exactly as
        `experiments/students/grade.py` check 2 replays: the child re-runs the
        same program with `replay_effects` and prints its receipts, and they are
        the bytes this process recorded -- everything but the two fields a clock
        decides (`fixture_effects.VOLATILE_RECEIPT_FIELDS`).
        """
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as second:
            pcr, pxc, run = run_once(root)
            record = record_of(pcr, pxc, run)
            record_path = os.path.join(root, "record.json")
            with open(record_path, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(record, handle, indent=2, sort_keys=True)

            completed = replay_in_a_fresh_process(record_path, second)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, comparable_receipts(run) + "\n")
            # The write really happened again, in the replay's own root, and the
            # bytes are the recorded bytes -- that is what re-digesting bought.
            with open(os.path.join(second, "out", "note.txt"), encoding="utf-8") as handle:
                self.assertEqual(handle.read(), NOTE_TEXT)

    def test_the_replayed_receipt_carries_the_recorded_ledger(self):
        """The in-process half of the same claim, stated without a subprocess."""
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as second:
            pcr, pxc, run = run_once(root)
            record = record_of(pcr, pxc, run)
            again = build_program()
            store = PxC()
            replayed = again.run(
                store,
                observe=True,
                effects_root=second,
                replay_effects=ledgers_from_record(record),
            )
            self.assertEqual(
                [dataclasses.asdict(e) for e in replayed.receipts["stamp"].effects],
                [dataclasses.asdict(e) for e in run.receipts["stamp"].effects],
            )
            self.assertEqual(
                replayed.receipts["stamp"].result_sha256, run.receipts["stamp"].result_sha256
            )
            self.assertEqual(comparable_receipts(replayed), comparable_receipts(run))


class Tampering(unittest.TestCase):
    """What a replay does when the record and the world disagree."""

    def test_a_tampered_effect_digest_is_refused_naming_the_invocation_and_index(self):
        """effects.py:ReplayEffects._next -- an entry that fails its own digest.

        One hex character of one `result_sha256` in the record, and the fresh
        process refuses rather than replaying: the refusal names the invocation
        (`stamp`), the kind (`now_ms`) and the index (1).
        """
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as second:
            pcr, pxc, run = run_once(root)
            record = record_of(pcr, pxc, run)
            entry = record["ticks"][0]["invocations"][0]["effects"][1]
            self.assertEqual(entry["kind"], "now_ms")
            digest = entry["result_sha256"]
            entry["result_sha256"] = ("b" if digest[0] == "a" else "a") + digest[1:]
            record_path = os.path.join(root, "tampered.json")
            with open(record_path, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(record, handle, indent=2, sort_keys=True)

            completed = replay_in_a_fresh_process(record_path, second)
            self.assertEqual(completed.returncode, 1, completed.stdout)
            self.assertIn("EffectRefused", completed.stderr)
            self.assertIn("calculation 'stamp'", completed.stderr)
            self.assertIn("effect 1 (now_ms)", completed.stderr)
            self.assertIn("does not match its own digest", completed.stderr)

    def test_a_write_whose_text_changed_is_refused(self):
        """effects.py:ReplayEffects.write_text -- the one effect that is re-performed."""
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as second:
            pcr, pxc, run = run_once(root)
            record = record_of(pcr, pxc, run)
            # The same program, writing something else: the replay re-digests and
            # refuses instead of reporting an equal run.
            other = build_program("a different note\n")
            with self.assertRaises(EffectRefused) as caught:
                other.run(
                    PxC(),
                    observe=True,
                    effects_root=second,
                    replay_effects=ledgers_from_record(record),
                )
            self.assertIn("calculation 'stamp'", str(caught.exception))
            self.assertIn("effect 0 (write_text)", str(caught.exception))
            self.assertIn(record["ticks"][0]["invocations"][0]["effects"][0]["result_sha256"],
                          str(caught.exception))

    def test_an_extra_effect_on_replay_is_refused(self):
        """effects.py:ReplayEffects._next -- the ledger ends and the program does not."""
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as second:
            pcr, pxc, run = run_once(root)
            ledger = [dataclasses.asdict(e) for e in run.receipts["stamp"].effects]

            def greedy(args):
                effects = args["effects"]
                effects.write_text(NOTE_PATH, args["note"])
                effects.now_ms()
                effects.random(1)
                effects.random(1)
                return effects.env("PATH")

            greedier = PCR("greedy")
            greedier.calc(
                "Stamp",
                Calculation("oc.effects.greedy", greedy),
                id="stamp",
                into=STAMP,
                args={"note": NOTE_TEXT},
            )
            with self.assertRaises(EffectRefused) as caught:
                greedier.run(
                    PxC(), observe=True, effects_root=second, replay_effects={"stamp": ledger}
                )
            self.assertIn("effect 5 (env)", str(caught.exception))
            self.assertIn("asked for one more", str(caught.exception))

    def test_a_replay_that_performs_fewer_effects_is_refused(self):
        """pcr.py:_prepare -- an unspent ledger is a divergence too, and is named."""
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as second:
            pcr, pxc, run = run_once(root)
            ledger = [dataclasses.asdict(e) for e in run.receipts["stamp"].effects]

            def lazy(args):
                args["effects"].write_text(NOTE_PATH, args["note"])
                return {"path": NOTE_PATH}

            lazier = PCR("lazy")
            lazier.calc(
                "Stamp",
                Calculation("oc.effects.lazy", lazy),
                id="stamp",
                into=STAMP,
                args={"note": NOTE_TEXT},
            )
            with self.assertRaisesRegex(ValueError, "replayed 1 of 5 recorded effect"):
                lazier.run(
                    PxC(), observe=True, effects_root=second, replay_effects={"stamp": ledger}
                )

    def test_a_replay_with_no_ledger_for_an_oc_is_refused(self):
        """pcr.py:_effects_handle -- a replay that performed a real effect is not one."""
        with tempfile.TemporaryDirectory() as root:
            pcr = build_program()
            with self.assertRaisesRegex(ValueError, "carries no ledger for it"):
                pcr.run(PxC(), observe=True, effects_root=root, replay_effects={})


class PurityIsAMissingHandle(unittest.TestCase):
    """`fn` gets no handle; `oc` is the only other root; nothing else registers."""

    def test_the_two_roots_and_no_third(self):
        """core.py:Calculation.__post_init__ -- `fn.`, `oc.`, and nothing else.

        Mutation: `startswith(CALCULATION_ROOTS)` -> `startswith("")` and this
        fails at the first refusal.
        """
        self.assertFalse(Calculation("fn.a.b", lambda args: 1).is_operational)
        self.assertTrue(Calculation("oc.a.b", lambda args: 1).is_operational)
        for address in ("px.a.b", "double", "", "OC.a.b", "fn", "oc"):
            with self.assertRaises(ValueError) as caught:
                Calculation(address, lambda args: 1)
            self.assertIn("must start with 'fn.'", str(caught.exception))
            self.assertIn("'oc.'", str(caught.exception))

    def test_a_pure_calculation_gets_no_handle(self):
        """pcr.py:_prepare -- the key is not there, so reading it raises KeyError.

        Mutation: pass the handle to every Calculation instead of to an `oc.`
        only, and this fails -- the fn reads `args["effects"]` and gets one.
        """
        seen = {}

        def peek(args):
            seen["keys"] = sorted(args)
            return args["effects"]

        pcr = PCR("impure-fn")
        pcr.calc("T", Calculation("fn.effects.peek", peek), id="p", into=Part("scratch.x"))
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(KeyError):
                pcr.run(PxC(), observe=True, effects_root=root)
        self.assertEqual(seen["keys"], [])

    def test_an_oc_is_called_with_the_handle_under_effects(self):
        """pcr.py:_prepare -- and a program cannot shadow it with an arg of its own."""
        seen = {}

        def look(args):
            seen["handle"] = args["effects"]
            seen["keys"] = sorted(args)
            return 1

        pcr = PCR("oc-args")
        pcr.calc(
            "T",
            Calculation("oc.effects.look", look),
            id="o",
            into=Part("scratch.x"),
            args={"effects": "a forgery"},
        )
        with tempfile.TemporaryDirectory() as root:
            pcr.run(PxC(), observe=True, effects_root=root)
        self.assertIsInstance(seen["handle"], Effects)
        self.assertEqual(seen["keys"], ["effects"])

    def test_an_oc_without_an_effects_root_refuses_the_run(self):
        """pcr.py:_effects_handle -- no root, no world, no run."""
        pcr = build_program()
        with self.assertRaisesRegex(ValueError, "was given no effects_root"):
            pcr.run(PxC(), observe=True)


class ObserveOnAndOff(unittest.TestCase):
    """Observation is additive; the ledger is not an observation."""

    def test_the_testimony_is_byte_identical_with_observation_on_and_off(self):
        """pcr.py:PcrRun -- `ticks` is the program, and effects are not in it."""
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            _, _, observed = run_once(a, observe=True)
            _, _, plain = run_once(b, observe=False)
            self.assertEqual(
                json.dumps([dataclasses.asdict(t) for t in plain.ticks], sort_keys=True),
                json.dumps([dataclasses.asdict(t) for t in observed.ticks], sort_keys=True),
            )
            self.assertEqual(plain.receipts, {})

    def test_the_effects_are_recorded_with_observation_off(self):
        """pcr.py:PcrRun.effects -- an effect is what happened, not what was watched."""
        with tempfile.TemporaryDirectory() as root:
            _, _, plain = run_once(root, observe=False)
            self.assertEqual(
                tuple(effect.kind for effect in plain.effects["stamp"]), EXPECTED_KINDS
            )

    def test_a_replay_of_an_unobserved_run_is_the_same_replay(self):
        """The ledger is enough: replay does not need the run that made it observed."""
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as second:
            _, _, plain = run_once(root, observe=False)
            ledgers = {
                invocation_id: [dataclasses.asdict(e) for e in ledger]
                for invocation_id, ledger in plain.effects.items()
            }
            replayed = build_program().run(
                PxC(), observe=True, effects_root=second, replay_effects=ledgers
            )
            self.assertEqual(replayed.results["stamp"], plain.results["stamp"])


class ParallelEffects(unittest.TestCase):
    """An `oc` in a parallel Tick: refused, unless the program says it checked."""

    def test_an_oc_in_a_parallel_tick_is_refused(self):
        """pcr.py:_refuse_parallel_effects ({?} ParallelEffectsOptIn).

        The simplest honest rule: effects from two branches at once are safe only
        when they are file writes to distinct paths, and the kernel cannot know
        that before they run.
        """
        pcr = build_program()
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "allow_parallel_effects=True"):
                pcr.run(PxC(), observe=True, parallel=True, effects_root=root)

    def test_the_refusal_is_before_anything_of_the_tick_runs(self):
        """Refused at the Tick boundary: the store and the world are untouched."""
        with tempfile.TemporaryDirectory() as root:
            pxc = PxC()
            with self.assertRaises(ValueError):
                build_program().run(pxc, observe=True, parallel=True, effects_root=root)
            self.assertEqual(pxc.addresses(), ())
            self.assertEqual(os.listdir(root), [])

    def test_allow_parallel_effects_runs_it_and_records_the_same_ledger(self):
        """The opt-in is the whole difference; the ledger is what a serial run's was."""
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            _, _, serial = run_once(a)
            parallel = build_program().run(
                PxC(),
                observe=True,
                parallel=True,
                effects_root=b,
                allow_parallel_effects=True,
            )
            self.assertEqual(
                tuple(e.kind for e in parallel.receipts["stamp"].effects), EXPECTED_KINDS
            )
            self.assertEqual(
                json.dumps([dataclasses.asdict(t) for t in serial.ticks], sort_keys=True),
                json.dumps([dataclasses.asdict(t) for t in parallel.ticks], sort_keys=True),
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
