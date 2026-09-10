"""The one-address program whose receipt and record are pinned byte for byte.

Written *before* multi-produce landed and imported by both the generator that
wrote `fixtures/single_into_pre_change.json` and the test that reads it, so the
pinned bytes and the bytes under test come from the same source text: the
Calculation body below is what `FrozenCalculation.implementation_sha256`
digests, so a copy of it in two files would pin two different digests.

Not named `test_*.py`: `unittest discover -s tests` must not collect it.
"""

from __future__ import annotations

import json

from pyto import Calculation, PCR, Part, PxC


def fixture_take(args):
    return args["value"]


FIXTURE_TAKE = Calculation("fn.fixture.take", fixture_take)


def build():
    """Two one-address invocations: a `px:` binding and an `fn:` binding.

    `report` binds `Part("out.v")`, which `PCR.calc` rewrites into the writer's
    ResultRef, so the record carries both testimony spellings -- the pair the
    multi-produce change had to leave alone.
    """
    pxc = PxC()
    pxc.set(Part("input.v"), 3)
    pcr = PCR("fixture")
    pcr.calc("Prepare", FIXTURE_TAKE, id="take", value=Part("input.v"), into=Part("out.v"))
    pcr.calc("Report", FIXTURE_TAKE, id="report", value=Part("out.v"), into="out.copy")
    return pcr, pxc


def normalize(payload):
    """Blank every field that is a clock or an installation, in place, and return it.

    Durations, start times and the wall clock differ run to run; the runtime
    version differs between a checkout and a wheel. Everything else in the
    receipt and the record is the claim being pinned.
    """
    receipt = payload["receipt"]
    receipt["started_ms"] = None
    receipt["duration_ms"] = None
    record = payload["record"]
    record["source"]["version"] = "<version>"
    record["counters"]["wall_ms"] = None
    for tick in record["ticks"]:
        for invocation in tick["invocations"]:
            invocation["duration_ms"] = None
    return payload


def payload():
    """`{"receipt": ..., "record": ...}` for the program above, normalized."""
    from dataclasses import asdict

    from pyto.materialize import run_record

    pcr, pxc = build()
    run = pcr.run(pxc, observe=True)
    record = run_record(run, pxc, preexisting={"input.v"})
    return normalize({"receipt": asdict(run.receipts["take"]), "record": record})


def dumps(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"
