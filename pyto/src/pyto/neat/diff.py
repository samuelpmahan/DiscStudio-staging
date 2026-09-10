"""fn.neat.diff.candidates: the difference between two PQL documents, computed before
it is shown.

The owner's rule this module exists to satisfy: "Find meaningful differentiation
either through pure calculation or questions." A diff is pure calculation -- no
mining, no judgement call about what matters -- and it runs *before* anyone looks
at two candidate documents side by side, not after, so what a person sees is
already reduced to what actually changed.

A "PQL document" here is the browser ``readPql`` shape (grammar transcribed at
``pyto/experiments/grouped-ablation/pql_document.py``, reached from Python only as
data)::

    {"Ticks": [{"name": <str>,
                "Calculations": [{"call": "fn.<...>", "with": {name: address},
                                   "args": {...}, "into": address | [address, ...]}]}],
     "labels": [<str>, ...]}   # optional, presentation only

``labels`` is this module's own addition to that shape (the JS grammar does not
read it and never will): a list of strings that describe a document to a human
and never change what it computes, so ``structural_digest`` strips it before
digesting -- two documents that differ only in their labels are one document as
far as this module is concerned.

``candidates`` (``fn.neat.diff.candidates``) takes two such documents, a seed
store (address -> value) and a registry (address -> a registered ``fn.``
Calculation), and publishes one Part, ``px.exp.blok.diff.<a>.<b>`` where ``a``
and ``b`` are the first 16 hex digits of each document's structural digest. When
neither document names an ``oc.`` Calculation, both are run -- one Python PCR per
document, built by ``run_document`` below -- and every address either declares as
``into`` is compared by value digest between the two runs. A document that names
an ``oc.`` Calculation is never run (an effect is not diffable by re-running it),
and every declared output is reported ``"unknown"`` instead.

One digest rule throughout, reused rather than reinvented
(``pyto/experiments/grouped-ablation/retain.py`` ``canonical_json``/``digest_of``):
sha256 of ``json.dumps(value, sort_keys=True, separators=(",", ":"))``, or no
digest at all when JSON cannot describe the value. Same inputs, same bytes: this
module reads no clock, no network, and no human text, so ``candidates`` run twice
on the same arguments returns the same dict, key for key and byte for byte once
serialized.

CLI::

    python -m pyto.neat.diff <a.json> <b.json> --store seed.json \\
        --registry <module>:<attribute> [--label-a TEXT] [--label-b TEXT]

``--registry`` names a module-level attribute (an address -> Calculation mapping)
by ``<module>:<attribute>``, imported with this repository's ``pyto/`` on
``sys.path`` so a fixture registry under ``pyto/tests/`` resolves the same way a
project registry under ``pyto/experiments/`` would. The CLI prints the diff value
as pretty (sorted-key, two-space indent) JSON -- the terminal spelling
``pyto.px`` already uses for a value a person is meant to read -- and writes the
Part to ``pyto/experiments/review/diffs/<a>-<b>.json``. When both documents were
run, the two run records (``pyto.materialize.run_record``, ``observe=True``) are
saved beside it as ``<a>-<b>.a.record.json`` and ``<a>-<b>.b.record.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
from typing import Any, Mapping

from ..core import Calculation, Part, PxC
from ..materialize import run_record, write_record
from ..pcr import PCR, PcrRun

HERE = os.path.dirname(os.path.abspath(__file__))  # pyto/src/pyto/neat
PYTO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # pyto/
DIFFS_DIR = os.path.join(PYTO_ROOT, "experiments", "review", "diffs")

ADDRESS_TEMPLATE = "px.exp.blok.diff.{a}.{b}"


# --------------------------------------------------------------------------- digests


def _canonical_json(value: Any) -> str:
    """The one digest rule's input form (retain.py ``canonical_json``, reused)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest_of(value: Any) -> str | None:
    """sha256 hex of the canonical JSON, or None when JSON cannot describe the value
    (retain.py ``digest_of``, reused, not reinvented)."""
    try:
        text = _canonical_json(value)
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def structural_digest(document: Mapping[str, Any]) -> str:
    """sha256 hex of ``document``'s canonical JSON with any top-level ``labels`` removed.

    Raises if the document (minus labels) is not JSON-describable -- a document
    that came from ``json.load`` always is, so this only ever fires on a
    hand-built document a caller passed something stranger than JSON into.
    """
    stripped = {key: value for key, value in document.items() if key != "labels"}
    digest = _digest_of(stripped)
    if digest is None:
        raise ValueError("structural_digest: document is not JSON-describable")
    return digest


# --------------------------------------------------------------------------- documents


def _declared_into(document: Mapping[str, Any]) -> list[str]:
    """Every address any Calculation in ``document`` publishes, in declared order."""
    addresses: list[str] = []
    for tick in document.get("Ticks", []):
        for entry in tick.get("Calculations", []):
            into = entry.get("into")
            if into is None:
                continue
            if isinstance(into, (list, tuple)):
                addresses.extend(into)
            else:
                addresses.append(into)
    return addresses


def _oc_calls(document: Mapping[str, Any]) -> list[str]:
    """Every ``oc.`` call address in ``document``, in declared order (one entry per
    occurrence -- a document naming the same oc. call twice is not deduplicated,
    since that is itself something the remainder is honest about)."""
    calls: list[str] = []
    for tick in document.get("Ticks", []):
        for entry in tick.get("Calculations", []):
            call = entry.get("call", "")
            if isinstance(call, str) and call.startswith("oc."):
                calls.append(call)
    return calls


def run_document(
    document: Mapping[str, Any],
    store: Mapping[str, Any],
    registry: Mapping[str, Calculation[Any, Any]],
    pcr_name: str,
) -> tuple[PcrRun, PxC]:
    """Build and run one PCR from a readPql document: one Tick per document Tick, one
    invocation per Calculation entry, in declared order, seeded from ``store``.

    A ``with`` binding is always ``Part(address)`` -- never a hand-built ``ResultRef``
    -- because ``PCR.calc`` already turns a Part this same PCR previously wrote into
    that writer's ``ResultRef`` (``src/pyto/pcr.py`` ``PCR.calc``, the ``self._writers``
    lookup), which is exactly "the sibling's ResultRef when the address is an earlier
    sibling's into". Run with ``observe=True`` so every invocation leaves a receipt and
    the run can be materialized into a ``pyto-run-record@1`` document.
    """
    pxc = PxC()
    for address, value in dict(store or {}).items():
        pxc.set(Part(address), value)
    pcr = PCR(pcr_name)
    counter = 0
    for tick in document.get("Ticks", []):
        tick_name = tick["name"]
        for entry in tick.get("Calculations", []):
            counter += 1
            call = entry["call"]
            calculation = registry[call]
            bindings = {
                name: Part(address) for name, address in (entry.get("with") or {}).items()
            }
            pcr.calc(
                tick_name,
                calculation,
                id=f"c{counter}",
                into=entry.get("into"),
                args=dict(entry.get("args") or {}),
                **bindings,
            )
    run = pcr.run(pxc, observe=True)
    return run, pxc


def _compare_outputs(
    doc_a: Mapping[str, Any],
    doc_b: Mapping[str, Any],
    store: Mapping[str, Any],
    registry: Mapping[str, Calculation[Any, Any]],
) -> dict[str, str]:
    """Run both documents and compare every declared ``into`` address by value digest.

    An address declared by only one of the two documents has nothing on the other
    side to compare against; the four-word vocabulary this module reports
    (``same``/``changed``/``new``/``unknown``) has no fifth word for "removed", so
    such an address -- on either side -- is reported ``"new"``: it is new *to this
    comparison*, not necessarily new to document ``b`` ({?} DiffNewIsAsymmetric).
    """
    run_a, pxc_a = run_document(doc_a, store, registry, "neat.diff.a")
    run_b, pxc_b = run_document(doc_b, store, registry, "neat.diff.b")
    into_a, into_b = set(_declared_into(doc_a)), set(_declared_into(doc_b))
    outputs: dict[str, str] = {}
    for address in sorted(into_a | into_b):
        if address in into_a and address in into_b:
            same = _digest_of(pxc_a.get(address)) == _digest_of(pxc_b.get(address))
            outputs[address] = "same" if same else "changed"
        else:
            outputs[address] = "new"
    return outputs


def candidates(args: Mapping[str, Any]) -> dict[str, Any]:
    """fn.neat.diff.candidates.

    ``args``: ``doc_a``, ``doc_b`` (readPql documents, each may carry its own
    top-level ``labels`` list), ``store`` (address -> seed value, optional), and
    ``registry`` (address -> registered ``fn.`` Calculation).
    """
    doc_a, doc_b = args["doc_a"], args["doc_b"]
    store = args.get("store") or {}
    registry = args["registry"]

    digest_a, digest_b = structural_digest(doc_a), structural_digest(doc_b)
    structural = "same" if digest_a == digest_b else "different"

    oc_a, oc_b = _oc_calls(doc_a), _oc_calls(doc_b)
    remainder = list(doc_a.get("labels") or []) + list(doc_b.get("labels") or [])
    remainder += [f"not run: {call} is oc." for call in oc_a + oc_b]

    if oc_a or oc_b:
        declared = sorted(set(_declared_into(doc_a)) | set(_declared_into(doc_b)))
        outputs = {address: "unknown" for address in declared}
    else:
        outputs = _compare_outputs(doc_a, doc_b, store, registry)

    return {
        "structural": structural,
        "a": digest_a,
        "b": digest_b,
        "outputs": outputs,
        "remainder": remainder,
    }


CANDIDATES = Calculation("fn.neat.diff.candidates", candidates)


# --------------------------------------------------------------------------- CLI


def _load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _with_label(document: Mapping[str, Any], label: str | None) -> dict[str, Any]:
    if not label:
        return dict(document)
    out = dict(document)
    out["labels"] = list(out.get("labels") or []) + [label]
    return out


def _load_registry(spec: str) -> Mapping[str, Calculation[Any, Any]]:
    """``<module>:<attribute>`` -> the attribute (an address -> Calculation mapping),
    importing with ``pyto/`` on ``sys.path`` so ``tests.fixtures.blok.registry`` and a
    project registry under ``experiments/`` both resolve the same way."""
    if ":" not in spec:
        raise ValueError(f"--registry must be '<module>:<attribute>', got {spec!r}")
    module_name, attr_path = spec.rsplit(":", 1)
    if PYTO_ROOT not in sys.path:
        sys.path.insert(0, PYTO_ROOT)
    module = importlib.import_module(module_name)
    value: Any = module
    for part in attr_path.split("."):
        value = getattr(value, part)
    return value


def _write_part(address: str, value: Any, path: str) -> None:
    """One Part on disk: ``{"address", "value", "sha256"}``, sorted keys, LF."""
    digest = _digest_of(value)
    if digest is None:
        raise ValueError(f"{address}: value is not JSON-describable, no sha256 to write")
    document = {"address": address, "value": value, "sha256": digest}
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pyto.neat.diff",
        description="the difference between two PQL documents, computed before it is shown",
    )
    parser.add_argument("a", help="path to the first document (readPql shape, JSON)")
    parser.add_argument("b", help="path to the second document (readPql shape, JSON)")
    parser.add_argument("--store", required=True, help="JSON object: address -> seed value")
    parser.add_argument(
        "--registry", required=True, help="<module>:<attribute>, an address -> Calculation mapping"
    )
    parser.add_argument("--label-a", default=None, help="presentation-only label for document a")
    parser.add_argument("--label-b", default=None, help="presentation-only label for document b")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    doc_a = _with_label(_load_json(args.a), args.label_a)
    doc_b = _with_label(_load_json(args.b), args.label_b)
    store = _load_json(args.store)
    registry = _load_registry(args.registry)

    pxc = PxC()
    pxc.register(CANDIDATES)
    value = pxc.call(
        CANDIDATES, {"doc_a": doc_a, "doc_b": doc_b, "store": store, "registry": registry}
    )

    digest_a, digest_b = value["a"][:16], value["b"][:16]
    address = ADDRESS_TEMPLATE.format(a=digest_a, b=digest_b)
    stem = f"{digest_a}-{digest_b}"

    os.makedirs(DIFFS_DIR, exist_ok=True)
    _write_part(address, value, os.path.join(DIFFS_DIR, f"{stem}.json"))

    if not (_oc_calls(doc_a) or _oc_calls(doc_b)):
        run_a, pxc_a = run_document(doc_a, store, registry, "neat.diff.a")
        run_b, pxc_b = run_document(doc_b, store, registry, "neat.diff.b")
        preexisting = set(store)
        write_record(
            run_record(run_a, pxc_a, preexisting=preexisting),
            os.path.join(DIFFS_DIR, f"{stem}.a.record.json"),
        )
        write_record(
            run_record(run_b, pxc_b, preexisting=preexisting),
            os.path.join(DIFFS_DIR, f"{stem}.b.record.json"),
        )

    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
