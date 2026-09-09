"""Day 5's cross-project hit: a second, deliberately different domain ("shelf": a
disc golf bag of discs, each with a stability number) that pins pyto, declares its
own Parts (`px.shelf.*`) and Calculations (`fn.shelf.*`), and additionally resolves
ONE material through the very same content-addressed store the ablation domain
(`pyto/experiments/grouped-ablation`) already wrote to: the seed-7, n=400 split of
`features.make_data`'s synthetic rows.

This answers `{?} CrossProjectReuse` (pyto/questions.md) and is the "second tiny
domain" research/ULTRACODE-WEEK.md's Reframing 3 names for Day 5: "A cross-project
hit: a second tiny domain in this repository pins pyto, reads the same store, and
shows a verified hit on material the first domain produced."

Nothing below except the SHARED_* block is this domain's own. SHARED_CALCULATION,
SHARED_REVISION and SHARED_SOURCE are imported/derived from grouped-ablation
(features.make_data, calculations.REGISTRY, pyto.pcr's own digest function) so the
content-addressed key run.py computes is -- by construction, not by convention --
identical to the one pyto/experiments/grouped-ablation/run_cached.py and its
committed evidence used for `fn.ablation.split` on the same fixture (SHARED_SEED=7,
SHARED_N=400, matching run_cached.py's own `SEED, N = 7, 400`). Nothing from
grouped-ablation's `run.py`, `run_cached.py` or `program.py` is imported here: this
directory has its own files by those same names, and importing THOSE would collide
on the bare module names "run"/"program"; `calculations.py` and `features.py` have
no such collision, so those are the only two grouped-ablation modules this domain
touches, plus `pyto.pcr`'s own digest helpers (installed package, not
experiment-local -- see pyto/experiments/tasks/17/packet.md, {?} PrivateHelperImport).
"""

from __future__ import annotations

import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

GROUPED_ABLATION = os.path.normpath(os.path.join(HERE, "..", "grouped-ablation"))
if GROUPED_ABLATION not in sys.path:
    # Appended, never inserted at 0: HERE must stay ahead of GROUPED_ABLATION so this
    # domain's own bare `import program`/`import run` (both directories have files by
    # those names) resolve to THIS directory's files, not grouped-ablation's. Only the
    # non-colliding bare names (materials, calculations, features) actually fall
    # through to GROUPED_ABLATION.
    sys.path.append(GROUPED_ABLATION)

from pyto import Calculation, PCR, Part  # noqa: E402
from pyto.pcr import _implementation_sha256  # noqa: E402  -- the exact digest PCR.run itself computes
# (pcr.py:349-351 calls this very function on the invocation's Calculation.calculate); imported, not
# reimplemented, so SHARED_REVISION below is guaranteed identical to what the ablation domain's own
# receipts recorded for fn.ablation.split, never an independent recomputation that could drift.

from calculations import REGISTRY as ABLATION_REGISTRY  # noqa: E402  -- grouped-ablation/calculations.py;
# only REGISTRY["fn.ablation.split"] is used below, imported and called, never reimplemented.
from features import make_data  # noqa: E402  -- grouped-ablation/features.py; the exact fixture builder
# the ablation domain used for fn.ablation.split.

# --------------------------------------------------------------------- the one shared material

SHARED_SEED = 7
SHARED_N = 400
SHARED_SOURCE = {"seed": SHARED_SEED, "n": SHARED_N}  # exactly run_cached.py's source={"seed": SEED, "n": N}
SHARED_CALCULATION: Calculation = ABLATION_REGISTRY["fn.ablation.split"]  # imported, never reimplemented
SHARED_REVISION = _implementation_sha256(SHARED_CALCULATION.calculate)  # identical to the receipt's
# implementation_sha256 for the "split" invocation (pyto/experiments/grouped-ablation/evidence/run-1/
# receipts.json and evidence/run-6-cached/reuse-ledger.json both record this same string).


def shared_split_args() -> dict:
    """{'rows': make_data(7, 400)} -- byte-identical to what run_experiment(7, 400)
    bound to fn.ablation.split, since make_data is a pure function of (seed, n)."""
    return {"rows": make_data(SHARED_SEED, SHARED_N)}


# --------------------------------------------------------------------- the shelf domain's own

BAG = Part("px.shelf.bag")
HISTOGRAM = Part("px.shelf.histogram")
CARRY = Part("px.shelf.carry")

DISC_NAMES: tuple[str, ...] = (
    "Eagle", "Firebird", "Zone", "Buzzz", "Wraith", "Destroyer",
    "Nuke", "Aviar", "Roc3", "Sidewinder", "Undertaker", "Tern",
)
STABILITY_CHOICES: tuple[int, ...] = (-3, -2, -1, 0, 1, 2, 3)  # integers only: bit-identical everywhere,
# no libm involved (features.py's _standard_normal docstring names exactly this concern for floats).
CARRY_THRESHOLD = 1  # |stability| <= this is "easy to throw", the toy pick criterion

# Explicit, literal revisions (materials.py's caller-supplies-it design, materials.py:48-55): this
# domain's own Calculations have no PCR receipt to read a revision off, so each names its own
# identity string. Changing either is a deliberate "this Calculation changed" signal and must miss
# the store (test_cross_project.py::RevisionChangeIsAMiss).
HISTOGRAM_REVISION = "fn.shelf.stabilityHistogram@v1"
CARRY_REVISION = "fn.shelf.pickToCarry@v1"


def make_bag(seed: int, n: int = 12) -> list[dict]:
    """n discs, each {'name', 'stability'}; deterministic per seed."""
    rng = random.Random(seed)
    names = DISC_NAMES[:n] if n <= len(DISC_NAMES) else DISC_NAMES + tuple(
        f"disc{i}" for i in range(len(DISC_NAMES), n)
    )
    return [{"name": name, "stability": rng.choice(STABILITY_CHOICES)} for name in names]


def stability_histogram(args: dict) -> dict:
    """Bucket the bag by stability: overstable (>=2), stable (-1..1), understable (<=-2)."""
    buckets = {"overstable": 0, "stable": 0, "understable": 0}
    for disc in args["bag"]:
        s = disc["stability"]
        if s >= 2:
            buckets["overstable"] += 1
        elif s <= -2:
            buckets["understable"] += 1
        else:
            buckets["stable"] += 1
    return buckets


def pick_to_carry(args: dict) -> list[str]:
    """Names of discs within CARRY_THRESHOLD of neutral stability, sorted."""
    threshold = args.get("threshold", CARRY_THRESHOLD)
    return sorted(disc["name"] for disc in args["bag"] if abs(disc["stability"]) <= threshold)


REGISTRY: dict[str, Calculation] = {
    "fn.shelf.stabilityHistogram": Calculation("fn.shelf.stabilityHistogram", stability_histogram),
    "fn.shelf.pickToCarry": Calculation("fn.shelf.pickToCarry", pick_to_carry),
}


def build_program(bag: list[dict]) -> PCR:
    """Wire the shelf domain's own two Calculations into one Tick over `bag`.

    Run for testimony only (mermaid.mmd, testimony.json); the materials-store
    resolutions (the shared split, then these two) are separate calls in run.py,
    mirroring run_cached.py's split of concerns: run the program for testimony,
    separately resolve values through the shared store.
    """
    pcr = PCR("shelf.bag")
    pcr.calc("Shelf", REGISTRY["fn.shelf.stabilityHistogram"], id="histogram", bag=BAG, into=HISTOGRAM)
    pcr.calc("Shelf", REGISTRY["fn.shelf.pickToCarry"], id="carry", bag=BAG, into=CARRY)
    return pcr
