"""build_program(variants) -> PCR with ticks Prepare / Fit / Score / Compare.

The variant family is unrolled by the experiment-local family() helper because
PCR.calc needs every invocation at authoring time (pcr.py:247-282); the selector
also runs inside the PCR so testimony records that the variant list is a
Calculation result, and run.py asserts the two agree.
"""

from __future__ import annotations

from pyto import PCR, Part

from calculations import REGISTRY

ROWS = Part("input.ablation.rows")
GROUPS = Part("input.ablation.groups")
VARIANTS = Part("scratch.ablation.variants")
SPLIT = Part("scratch.ablation.split")
COMPARISON = Part("scratch.ablation.comparison")
BASELINE_KEY = "all"


def model_part(key: str) -> Part:
    return Part(f"scratch.ablation.model.{key}")


def score_part(key: str) -> Part:
    return Part(f"scratch.ablation.score.{key}")


def family(pcr: PCR, variants: list[dict]) -> dict[str, Part]:
    """Add one fit+score invocation pair per variant.

    Ids fit.<key> / score.<key>; Parts scratch.ablation.model.<key> and
    scratch.ablation.score.<key>. Both bind split=SPLIT, which the PCR rewrites
    to ResultRef('split') because 'split' was declared as its writer earlier
    (pcr.py:261-265), so testimony records inputs['split'] == 'fn:split'.
    """
    scores: dict[str, Part] = {}
    for variant in variants:
        key = variant["key"]
        pcr.calc(
            "Fit",
            REGISTRY["fn.ablation.fit"],
            id=f"fit.{key}",
            split=SPLIT,
            args={"columns": list(variant["columns"]), "variant": key},
            into=model_part(key),
        )
        pcr.calc(
            "Score",
            REGISTRY["fn.ablation.score"],
            id=f"score.{key}",
            split=SPLIT,
            model=model_part(key),
            into=score_part(key),
        )
        scores[key] = score_part(key)
    return scores


def build_program(variants: list[dict], name: str = "ablation.grouped") -> PCR:
    pcr = PCR(name)
    pcr.calc("Prepare", REGISTRY["fn.ablation.selectVariants"], id="select", groups=GROUPS, into=VARIANTS)
    pcr.calc("Prepare", REGISTRY["fn.ablation.split"], id="split", rows=ROWS, into=SPLIT)
    scores = family(pcr, variants)
    pcr.calc(
        "Compare",
        REGISTRY["fn.ablation.compare"],
        id="compare",
        args={"baseline": BASELINE_KEY},
        into=COMPARISON,
        **scores,
    )
    return pcr
