"""The `oc` program every effects test turns on: one effect-ful Calculation, one pure one.

Imported by `tests/test_effects.py`, by the fresh-process replay child it starts,
and by the generator of the committed `px effects` fixture, so all three digest
the same source text: `FrozenCalculation.implementation_sha256` is the digest of
the function body below, and a copy of it in two files would pin two digests
(the reason `tests/fixture_single_into.py` exists, verbatim).

Not named `test_*.py`: `unittest discover -s tests` must not collect it.
"""

from __future__ import annotations

from pyto import PCR, Calculation, Part, PxC

NOTE = Part("scratch.effects.note")
STAMP = Part("scratch.effects.stamp")
REPORT = Part("scratch.effects.report")

NOTE_TEXT = "the receipt is the subject\n"
NOTE_PATH = "out/note.txt"


def effects_stamp(args):
    """Five effects: a write, a clock, a seed (drawn by the first random), two draws.

    The seed is not written by this Calculation and is not visible to it: it is
    drawn and recorded by the handle the first time `random` is called, which is
    what makes two draws replayable from the ledger alone.
    """
    effects = args["effects"]
    path = effects.write_text(NOTE_PATH, args["note"])
    at_ms = effects.now_ms()
    first = effects.random(1)
    second = effects.random(1)
    return {"path": path, "at_ms": at_ms, "draws": [first[0], second[0]]}


def effects_summarize(args):
    """Pure: it is handed the stamp's result and never touches the world."""
    stamp = args["stamp"]
    return {"path": stamp["path"], "draws": len(stamp["draws"])}


STAMP_OC = Calculation("oc.effects.stamp", effects_stamp)
SUMMARIZE_FN = Calculation("fn.effects.summarize", effects_summarize)


def build_program(note: str = NOTE_TEXT) -> PCR:
    """Two Ticks: the `oc` writes and reads the world, the `fn` reads its result."""
    pcr = PCR("effects-demo")
    stamp = pcr.calc("Stamp", STAMP_OC, id="stamp", into=STAMP, args={"note": note})
    pcr.calc("Summarize", SUMMARIZE_FN, id="summary", into=REPORT, stamp=stamp)
    return pcr


def seeded_store() -> PxC:
    """The store the program runs against: it needs nothing seeded, and says so."""
    return PxC()


# The fields a clock decides, dropped before two receipts are compared: the same
# cut `experiments/students/grade.py` makes for check 2 (`duration_ms`), plus the
# two the schedule decides. Everything else -- the digests, the ledger, the
# declared and actual access -- must be equal byte for byte across processes,
# which is the claim `tests/test_effects.py` makes about replay.
VOLATILE_RECEIPT_FIELDS = ("started_ms", "duration_ms", "placement")


def comparable_receipts(run) -> str:
    """Every Receipt of `run` as canonical JSON, without the volatile fields.

    Defined here, beside the program, so the parent process and the fresh-process
    child compare through one function and not through two copies of a rule.
    """
    import dataclasses
    import json

    receipts = {}
    for invocation_id, receipt in run.receipts.items():
        entry = dataclasses.asdict(receipt)
        for name in VOLATILE_RECEIPT_FIELDS:
            entry.pop(name, None)
        receipts[invocation_id] = entry
    return json.dumps(receipts, sort_keys=True, indent=2)


def ledgers_from_record(record) -> dict:
    """`{invocation id: effects list}` for every invocation of a record that has one.

    What `PCR.run(..., replay_effects=...)` takes: the record is the disk, the
    clock and the generator on replay (RECORD.md, "Effects").
    """
    return {
        invocation["id"]: invocation["effects"]
        for tick in record["ticks"]
        for invocation in tick["invocations"]
        if invocation.get("effects")
    }
