"""crisp: template gen for PxC-ore, tunable to imply or force decomposition.

The owner, 2026-09-10: "Like neat(not) and tidy, it has a TINY job it does VERY
well. It does template gen that is required to import into PxC-ore (more on
that later) and is tunable to imply or force decomposition. Variation through
PxC is key." PxC-ore is the store, ``px.*``.

Three commands, one shape passed between them -- **the composition proposal**,
one Part at ``proposal.neat.composition.<set>.<option>.<revision>``:

* ``crisp template`` emits one proposal, from a capability sentence and a
  store and a registry, either as a skeleton (no ``--pql``) or derived from a
  given PQL document (``--pql``).
* ``crisp vary`` makes new options from an existing proposal by changing one
  binding (Variation A) or substituting one Calculation with the same produce
  shape (Variation B) -- "variation through PxC", the owner's own words.
* ``crisp import`` runs a proposal's PQL (``pyto.neat.diff.run_document``,
  reused rather than rewritten) and writes what it produced into the store, as
  a run record and a ``store-after`` snapshot. Nothing enters the store except
  through a proposal that resolves: ``import`` refuses whatever ``--mode
  force`` would refuse.

The proposal's required fields (the owner's local ``composition_proposal_contract``)::

    capabilityDelta   the new behaviour a person or composition gains (the sentence)
    why               why this is being proposed
    existingParts     exact existing Part addresses read or reused, {address, sha256}
                       (sha256 is the value's digest, from the store)
    proposedParts     new Parts this composition would add, each
                       {address, meaning, valueShape, producer, consumers}
    existingCalculations   exact registered addresses, {address, sha256}
                       (sha256 is FrozenCalculation.implementation_sha256, pcr.py)
    proposedCalculations   Calculations that do not exist yet, each
                       {address, inputs, args, outputs, behavior, sourceBoundary}
    PQL               the readPql document ({"Ticks": [...]})
    inspection        what a person sees or does
    verification      what would be checked, and what each check protects
    decisions         agent choices made while building this proposal, and their
                       alternatives
    limits            what this proposal deliberately does not add or decide

Two digest rules, both already established elsewhere and repeated here rather
than imported across a module boundary (the way ``pyto/src/pyto/neat/diff.py``
repeats retain.py's rule): a **value** digest is sha256 of
``json.dumps(value, sort_keys=True, separators=(",", ":"))`` (retain.py
``canonical_json``/``digest_of``, ``neat/diff.py`` again); a Calculation's
**implementation** digest is ``pyto.pcr._implementation_sha256`` -- sha256 of
its function body -- reused directly, since it is exactly
``FrozenCalculation.implementation_sha256`` elsewhere in this codebase and a
second, divergent way to hash a function body would be worse than none.

**The registry convention** (documented here because ``crisp`` is the first
consumer that needs a Calculation's *argument names*, not just the callable):
a registry entry is either a bare ``Calculation`` -- as in
``tests/fixtures/blok/registry.py`` -- or a mapping
``{"calculation": Calculation, "inputs": [name, ...]}``, where ``inputs`` is
that Calculation's argument names in the order ``crisp template``'s skeleton
generator fills them from the Part addresses it found in the capability
sentence ({?} RegistryInputNames). A registry with no declared inputs still
works -- a skeleton's "with" is then a single ``{"{?}": "{?}"}`` slot -- but
cannot be filled automatically.

**The "{?}" sentinel.** Two places carry it, both only in ``--mode imply``:
an unresolved PQL name (a "with" binding or a "call" nothing could resolve),
and one placeholder line each in ``inspection``/``verification``/``decisions``/
``limits`` when crisp has nothing to say about them. ``--mode force`` never
writes one: it refuses at the point resolution fails, naming what did not
resolve, and a final scan over the whole proposal refuses anything left
("a proposal with any '{?}' left is refused") as a backstop for a hand-edited
or reused document that still carries one.

CLI::

    python -m pyto.crisp template "<capability sentence>" --store store.json \\
        --registry <module>:<attr> --set <name> [--mode imply|force] \\
        [--pql doc.json] [--out dir]
    python -m pyto.crisp vary <proposal.json> --store store.json \\
        --registry <module>:<attr> [--bindings] [--calculations] [--max N]
    python -m pyto.crisp import <proposal.json> --store store.json \\
        --registry <module>:<attr> --out run.json [--into store-after.json]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from collections.abc import Mapping as MappingABC
from typing import Any, Mapping

from .core import Calculation
from .materialize import run_record, write_record
from .neat.diff import _load_json, _load_registry, _write_part, run_document
from .pcr import _implementation_sha256

HERE = os.path.dirname(os.path.abspath(__file__))  # pyto/src/pyto
PYTO_ROOT = os.path.dirname(os.path.dirname(HERE))  # pyto/
PROPOSALS_DIR = os.path.join(PYTO_ROOT, "experiments", "review", "proposals")

ADDRESS_PREFIX = "proposal.neat.composition."
SLOT = "{?}"

PROSE_FIELDS = ("inspection", "verification", "decisions", "limits")


class CrispRefusal(ValueError):
    """``--mode force`` (or ``crisp import``, which refuses the same things) refused."""


# --------------------------------------------------------------------------- the digest rule


def _canonical_json(value: Any) -> str:
    """retain.py's ``canonical_json``, repeated (``neat/diff.py`` repeats it too)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest_of(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- small shared helpers


def _addresses(into: Any) -> tuple[str, ...]:
    """``into`` (or a "with" value): none, one address, or several -- always a tuple."""
    if into is None:
        return ()
    if isinstance(into, (list, tuple)):
        return tuple(into)
    return (into,)


def _last_segment(address: str) -> str:
    return address.rsplit(".", 1)[-1]


def _kind_of(value: Any) -> str | None:
    """The value kind Variation A groups by: number, string, list, mapping -- or None
    for anything else (bool included: JSON has no fifth kind here to put it in)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "mapping"
    return None


def _calc_of(entry: Any) -> Calculation[Any, Any]:
    if isinstance(entry, Calculation):
        return entry
    if isinstance(entry, MappingABC) and "calculation" in entry:
        return entry["calculation"]
    raise CrispRefusal(
        f"crisp: registry entry {entry!r} is neither a Calculation nor "
        "{'calculation': Calculation, 'inputs': [...]}"
    )


def _inputs_of(entry: Any) -> tuple[str, ...] | None:
    if isinstance(entry, MappingABC) and "inputs" in entry:
        return tuple(entry["inputs"])
    return None


def _plain_registry(registry: Mapping[str, Any]) -> dict[str, Calculation[Any, Any]]:
    return {address: _calc_of(entry) for address, entry in registry.items()}


def _existing_part_entry(address: str, store: Mapping[str, Any]) -> dict[str, Any]:
    return {"address": address, "sha256": _digest_of(store[address])}


def _existing_calc_entry(address: str, registry: Mapping[str, Any]) -> dict[str, Any]:
    calc = _calc_of(registry[address])
    return {"address": address, "sha256": _implementation_sha256(calc.calculate)}


def _proposed_part_placeholder(address: str) -> dict[str, Any]:
    return {"address": address, "meaning": SLOT, "valueShape": SLOT, "producer": SLOT, "consumers": []}


def _proposed_calc_placeholder(call: str, entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "address": call,
        "inputs": sorted((entry.get("with") or {}).keys()),
        "args": dict(entry.get("args") or {}),
        "outputs": list(_addresses(entry.get("into"))),
        "behavior": SLOT,
        "sourceBoundary": SLOT,
    }


def find_slot(value: Any, path: str = "value") -> str | None:
    """The first JSON path under ``value`` whose string contains the "{?}" sentinel,
    or None. The force-mode backstop: everything else refuses with a specific
    message naming what did not resolve; this catches whatever a specific check
    was not written to look at (an "args" value, a hand-edited proposal)."""
    if isinstance(value, MappingABC):
        for key in sorted(value):
            found = find_slot(value[key], f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = find_slot(item, f"{path}[{index}]")
            if found:
                return found
    elif isinstance(value, str):
        if SLOT in value:
            return path
    return None


def _write_json(obj: Any, path: str) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _rel(path: str) -> str:
    try:
        return os.path.relpath(os.path.abspath(path), os.getcwd())
    except ValueError:  # pragma: no cover - different drives on Windows
        return path


def _address_for(set_name: str, option: str, value: Mapping[str, Any]) -> tuple[str, str]:
    """``proposal.neat.composition.<set>.<option>.<revision>``, revision the first 12
    hex of the value's digest -- and the full digest, for the Part's own ``sha256``."""
    digest = _digest_of(value)
    address = f"{ADDRESS_PREFIX}{set_name}.{option}.{digest[:12]}"
    return address, digest


def _set_of(address: str) -> str:
    tail = address[len(ADDRESS_PREFIX):]
    set_name, _option, _revision = tail.rsplit(".", 2)
    return set_name


# --------------------------------------------------------------------------- classifying a PQL document


def classify_pql_imply(
    document: Mapping[str, Any], store: Mapping[str, Any], registry: Mapping[str, Any]
) -> tuple[list, list, list, list]:
    """existingParts/proposedParts/existingCalculations/proposedCalculations, derived
    from ``document`` alone: a "with" address is existing when it is in the store,
    else proposed; a "call" is existing when it is registered, else proposed.
    Unresolved names become "{?}" slots (owner intent), never a refusal."""
    existing_parts: dict[str, Any] = {}
    proposed_parts: dict[str, Any] = {}
    existing_calcs: dict[str, Any] = {}
    proposed_calcs: dict[str, Any] = {}
    for tick in document.get("Ticks", []):
        for entry in tick.get("Calculations", []):
            call = entry.get("call")
            if call in registry:
                existing_calcs.setdefault(call, _existing_calc_entry(call, registry))
            else:
                proposed_calcs.setdefault(call, _proposed_calc_placeholder(call, entry))
            for _name, address in (entry.get("with") or {}).items():
                for one in _addresses(address):
                    if one in store:
                        existing_parts.setdefault(one, _existing_part_entry(one, store))
                    else:
                        proposed_parts.setdefault(one, _proposed_part_placeholder(one))
    return (
        [existing_parts[a] for a in sorted(existing_parts)],
        [proposed_parts[a] for a in sorted(proposed_parts)],
        [existing_calcs[a] for a in sorted(existing_calcs)],
        [proposed_calcs[a] for a in sorted(proposed_calcs)],
    )


def _refuse_backwards_reads(document: Mapping[str, Any]) -> None:
    """Task 57's chain rule, for a PQL document nothing has built into a PCR yet
    (``pcr.py`` ``_refuse_backwards_read``/``experiments/molecules/molecules.py``
    ``chain_rule`` enforce the same rule once a program exists; a proposal is
    checked before it is one). A "with" binding to a Part a *later* sibling in the
    same Tick produces is refused; an earlier Tick's produce is always available."""
    for tick in document.get("Ticks", []):
        produced_in_tick: set[str] = set()
        for entry in tick.get("Calculations", []):
            produced_in_tick.update(_addresses(entry.get("into")))
        seen: set[str] = set()
        for entry in tick.get("Calculations", []):
            call = entry.get("call")
            for name, address in (entry.get("with") or {}).items():
                for one in _addresses(address):
                    if one in produced_in_tick and one not in seen:
                        raise CrispRefusal(
                            f"'{call}' reads '{one}' as '{name}', which a later sibling in "
                            f"Tick '{tick.get('name')}' produces; a Calculation may read what "
                            "an earlier sibling produced, not a later one (the chain rule, "
                            "task 57)"
                        )
            seen.update(_addresses(entry.get("into")))


def check_pql_force(
    document: Mapping[str, Any], store: Mapping[str, Any], registry: Mapping[str, Any]
) -> tuple[list, list]:
    """Force-mode validation: refuses the first "with" binding or "call" that does
    not resolve, naming it, and any backwards read. Returns (existingParts,
    existingCalculations) on success -- proposedParts/proposedCalculations are
    always empty here, because anything that would need one is a refusal instead."""
    _refuse_backwards_reads(document)
    existing_parts: dict[str, Any] = {}
    existing_calcs: dict[str, Any] = {}
    produced_before_this_tick = set(store)
    for tick in document.get("Ticks", []):
        produced_in_tick: set[str] = set()
        for entry in tick.get("Calculations", []):
            produced_in_tick.update(_addresses(entry.get("into")))
        seen: set[str] = set()
        for entry in tick.get("Calculations", []):
            call = entry.get("call")
            if call in registry:
                existing_calcs.setdefault(call, _existing_calc_entry(call, registry))
            else:
                raise CrispRefusal(
                    f"'{call}' is not a registered Calculation, and no proposedCalculation "
                    "declares its inputs and outputs"
                )
            for name, address in (entry.get("with") or {}).items():
                for one in _addresses(address):
                    if one in store:
                        existing_parts.setdefault(one, _existing_part_entry(one, store))
                    elif one in produced_before_this_tick or one in seen:
                        continue
                    else:
                        raise CrispRefusal(
                            f"'{call}' binds '{name}' to '{one}', which is not a store "
                            "address, an earlier sibling's produce, or a proposedPart with "
                            "a producer"
                        )
            seen.update(_addresses(entry.get("into")))
        produced_before_this_tick |= produced_in_tick
    return (
        [existing_parts[a] for a in sorted(existing_parts)],
        [existing_calcs[a] for a in sorted(existing_calcs)],
    )


# --------------------------------------------------------------------------- template


def _names_in_sentence(address: str, sentence: str, *, imply: bool) -> bool:
    """A store or registry address "the sentence names": verbatim, always; its last
    segment as a whole word, only in imply mode."""
    if address in sentence:
        return True
    if not imply:
        return False
    segment = _last_segment(address)
    return re.search(rf"\b{re.escape(segment)}\b", sentence, re.IGNORECASE) is not None


def _placeholder_prose(mode: str) -> dict[str, list[str]]:
    if mode == "force":
        return {field: [] for field in PROSE_FIELDS}
    return {
        "inspection": [f"{SLOT} Inspection: what a person would see or do is not yet specified"],
        "verification": [
            f"{SLOT} Verification: what would be checked, and what it protects, is not yet specified"
        ],
        "decisions": [f"{SLOT} Decisions: no agent choice has been made yet"],
        "limits": [f"{SLOT} Limits: not yet specified"],
    }


def build_skeleton_proposal(
    sentence: str, store: Mapping[str, Any], registry: Mapping[str, Any], set_name: str, mode: str
) -> dict[str, Any]:
    if mode == "force":
        raise CrispRefusal(
            "template needs --pql in force mode: a skeleton cannot resolve where each "
            "Calculation would write its result, so there is nothing for force mode to verify"
        )
    matched_parts = sorted(a for a in store if _names_in_sentence(a, sentence, imply=True))
    matched_calcs = sorted(a for a in registry if _names_in_sentence(a, sentence, imply=True))

    existing_parts = [_existing_part_entry(a, store) for a in matched_parts]
    existing_calcs = [_existing_calc_entry(a, registry) for a in matched_calcs]

    cursor = 0
    calc_entries = []
    for address in matched_calcs:
        input_names = _inputs_of(registry[address])
        with_: dict[str, str] = {}
        if input_names:
            for name in input_names:
                if cursor < len(matched_parts):
                    with_[name] = matched_parts[cursor]
                    cursor += 1
                else:
                    with_[name] = SLOT
        else:
            with_ = {SLOT: SLOT}
        calc_entries.append({"call": address, "with": with_, "args": {}, "into": SLOT})

    value: dict[str, Any] = {
        "capabilityDelta": sentence,
        "why": f"a capability sentence handed to `crisp template` in {mode} mode: {sentence!r}",
        "existingParts": existing_parts,
        "proposedParts": [],
        "existingCalculations": existing_calcs,
        "proposedCalculations": [],
        "PQL": {"Ticks": [{"name": set_name, "Calculations": calc_entries}]},
    }
    value.update(_placeholder_prose(mode))
    return value


def build_pql_proposal(
    sentence: str, document: Mapping[str, Any], store: Mapping[str, Any], registry: Mapping[str, Any], mode: str
) -> dict[str, Any]:
    if mode == "force":
        existing_parts, existing_calcs = check_pql_force(document, store, registry)
        proposed_parts: list = []
        proposed_calcs: list = []
    else:
        existing_parts, proposed_parts, existing_calcs, proposed_calcs = classify_pql_imply(
            document, store, registry
        )
    value: dict[str, Any] = {
        "capabilityDelta": sentence,
        "why": f"a PQL document handed to `crisp template` in {mode} mode: {sentence!r}",
        "existingParts": existing_parts,
        "proposedParts": proposed_parts,
        "existingCalculations": existing_calcs,
        "proposedCalculations": proposed_calcs,
        "PQL": document,
    }
    value.update(_placeholder_prose(mode))
    if mode == "force":
        slot = find_slot(value)
        if slot:
            raise CrispRefusal(f"proposal has an unresolved slot at {slot}")
    return value


def cmd_template(args: argparse.Namespace) -> int:
    store = _load_json(args.store)
    registry = _load_registry(args.registry)

    if args.pql:
        document = _load_json(args.pql)
        value = build_pql_proposal(args.sentence, document, store, registry, args.mode)
    else:
        value = build_skeleton_proposal(args.sentence, store, registry, args.set_name, args.mode)

    address, digest = _address_for(args.set_name, "root", value)
    out_dir = args.out or PROPOSALS_DIR
    path = os.path.join(out_dir, f"{args.set_name}.root.{digest[:12]}.json")
    _write_part(address, value, path)

    print(f"address: {address}")
    print(f"wrote:   {_rel(path)}")
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


# --------------------------------------------------------------------------- vary


def _slug_of(address: str) -> str:
    return _last_segment(address)


def _binding_options(pql: Mapping[str, Any], store: Mapping[str, Any]):
    """Variation A, in the deterministic order: tick index, calculation index, input
    name, then the alternate address."""
    for tick_index, tick in enumerate(pql.get("Ticks", [])):
        for calc_index, entry in enumerate(tick.get("Calculations", [])):
            with_ = entry.get("with") or {}
            for name in sorted(with_):
                address = with_[name]
                if not isinstance(address, str) or address not in store:
                    continue
                kind = _kind_of(store[address])
                if kind is None:
                    continue
                candidates = sorted(
                    a for a in store if a != address and _kind_of(store[a]) == kind
                )
                for candidate in candidates:
                    mutated = copy.deepcopy(pql)
                    mutated["Ticks"][tick_index]["Calculations"][calc_index]["with"][name] = candidate
                    change = f"binding {name}: {address} -> {candidate}"
                    yield candidate, change, mutated


def _resolved_args(entry: Mapping[str, Any], store: Mapping[str, Any]) -> dict[str, Any] | None:
    args: dict[str, Any] = dict(entry.get("args") or {})
    for name, address in (entry.get("with") or {}).items():
        if isinstance(address, str) and address in store:
            args[name] = store[address]
        else:
            return None
    return args


def _produce_count(value: Any) -> int:
    if isinstance(value, (MappingABC, list, tuple)):
        return len(value)
    return 1


def _calculation_options(pql: Mapping[str, Any], registry: Mapping[str, Any], store: Mapping[str, Any]):
    """Variation B, in the deterministic order: tick index, calculation index, then
    the alternate address. Same produce shape is measured by calling the candidate
    with this entry's own resolved inputs -- a candidate that errors on them, or
    produces a different number of values, is not an option; an `oc.` Calculation
    is never a candidate (never invoked here, or substituted in)."""
    plain = _plain_registry(registry)
    for tick_index, tick in enumerate(pql.get("Ticks", [])):
        for calc_index, entry in enumerate(tick.get("Calculations", [])):
            call = entry.get("call")
            target = len(_addresses(entry.get("into")))
            args = _resolved_args(entry, store)
            if args is None:
                continue
            for candidate in sorted(plain):
                if candidate == call or candidate.startswith("oc."):
                    continue
                try:
                    result = plain[candidate].calculate(args)
                except Exception:
                    continue
                if _produce_count(result) != target:
                    continue
                mutated = copy.deepcopy(pql)
                mutated["Ticks"][tick_index]["Calculations"][calc_index]["call"] = candidate
                change = f"call: {call} -> {candidate}"
                yield candidate, change, mutated


def cmd_vary(args: argparse.Namespace) -> int:
    proposal = _load_json(args.proposal)
    base_value = proposal["value"]
    set_name = _set_of(proposal["address"])
    store = _load_json(args.store)
    registry = _load_registry(args.registry)
    pql = base_value["PQL"]

    only_one = args.bindings or args.calculations
    do_bindings = args.bindings or not only_one
    do_calcs = args.calculations or not only_one

    options = []
    if do_bindings:
        for index, (candidate, change, mutated) in enumerate(_binding_options(pql, store), start=1):
            options.append((f"a{index}-{_slug_of(candidate)}", change, mutated))
    if do_calcs:
        for index, (candidate, change, mutated) in enumerate(
            _calculation_options(pql, registry, store), start=1
        ):
            options.append((f"b{index}-{_slug_of(candidate)}", change, mutated))

    cut = 0
    if args.max is not None and len(options) > args.max:
        cut = len(options) - args.max
        options = options[: args.max]

    out_dir = os.path.dirname(os.path.abspath(args.proposal))
    for slug, change, mutated in options:
        existing_parts, proposed_parts, existing_calcs, proposed_calcs = classify_pql_imply(
            mutated, store, registry
        )
        value = dict(base_value)
        value.update(
            {
                "existingParts": existing_parts,
                "proposedParts": proposed_parts,
                "existingCalculations": existing_calcs,
                "proposedCalculations": proposed_calcs,
                "PQL": mutated,
            }
        )
        address, digest = _address_for(set_name, slug, value)
        path = os.path.join(out_dir, f"{set_name}.{slug}.{digest[:12]}.json")
        _write_part(address, value, path)
        print(f"{address}  {change}  digest={digest}")

    if cut:
        print(f"... {cut} more option(s) cut by --max {args.max}")
    return 0


# --------------------------------------------------------------------------- import


def cmd_import(args: argparse.Namespace) -> int:
    proposal = _load_json(args.proposal)
    value = proposal["value"]
    document = value["PQL"]
    store = _load_json(args.store)
    registry = _load_registry(args.registry)

    # import implies force: refuse whatever force mode would refuse, before running
    # anything -- nothing enters the store except through a proposal that resolves.
    check_pql_force(document, store, registry)
    slot = find_slot(value)
    if slot:
        raise CrispRefusal(f"proposal has an unresolved slot at {slot}")

    plain = _plain_registry(registry)
    run, pxc = run_document(document, store, plain, "crisp.import")
    record = run_record(run, pxc, preexisting=set(store))
    write_record(record, args.out)

    into_addresses = sorted(
        {
            address
            for tick in document.get("Ticks", [])
            for entry in tick.get("Calculations", [])
            for address in _addresses(entry.get("into"))
        }
    )
    store_after = {
        address: {"value": pxc.get(address), "sha256": _digest_of(pxc.get(address))}
        for address in into_addresses
    }
    into_path = args.into or os.path.join(
        os.path.dirname(os.path.abspath(args.out)) or ".", "store-after.json"
    )
    _write_json(store_after, into_path)

    invocation_count = sum(len(tick.calculations) for tick in run.ticks)
    print(f"ran:         {run.pcr} ({invocation_count} invocation(s))")
    print(f"record:      {_rel(args.out)}")
    print(f"store-after: {_rel(into_path)}")
    for address in into_addresses:
        print(f"  {address}  sha256={store_after[address]['sha256']}")
    return 0


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pyto.crisp",
        description="template gen required to import into PxC-ore, tunable to imply or force decomposition",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    template = sub.add_parser("template", help="emit one composition proposal Part")
    template.add_argument("sentence", help="the capability sentence (capabilityDelta)")
    template.add_argument("--store", required=True, help="JSON object: address -> value")
    template.add_argument("--registry", required=True, help="<module>:<attribute>")
    template.add_argument("--set", dest="set_name", required=True, help="the proposal's set name")
    template.add_argument("--mode", choices=["imply", "force"], default="imply")
    template.add_argument("--pql", default=None, help="a readPql document to derive the proposal from")
    template.add_argument("--out", default=None, help="directory to write the proposal Part in")

    vary = sub.add_parser("vary", help="variation through PxC: new options from an existing proposal")
    vary.add_argument("proposal", help="path to a proposal Part written by `crisp template`")
    vary.add_argument("--store", required=True)
    vary.add_argument("--registry", required=True)
    vary.add_argument("--bindings", action="store_true", help="only Variation A (change one binding)")
    vary.add_argument(
        "--calculations", action="store_true", help="only Variation B (substitute one Calculation)"
    )
    vary.add_argument("--max", type=int, default=None, help="cap the number of options printed and written")

    imp = sub.add_parser("import", help="run a proposal's PQL and write its Parts into the store")
    imp.add_argument("proposal", help="path to a proposal Part written by `crisp template`")
    imp.add_argument("--store", required=True)
    imp.add_argument("--registry", required=True)
    imp.add_argument("--out", required=True, help="where to write the run record")
    imp.add_argument("--into", default=None, help="where to write store-after.json (default: beside --out)")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "template":
            return cmd_template(args)
        if args.command == "vary":
            return cmd_vary(args)
        if args.command == "import":
            return cmd_import(args)
    except CrispRefusal as refused:
        print(f"crisp: {refused}", file=sys.stderr)
        return 1
    raise AssertionError(f"unreachable: unknown command {args.command!r}")  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
