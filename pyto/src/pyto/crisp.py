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
import html
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


# --------------------------------------------------------------------------- P&C: pnc and review
#
# The owner, 2026-09-10: "Can the digest be called P&C as a reminder?" Two digests
# on every proposal, card and option -- ``pnc`` over the mechanism (the PQL's
# Ticks, and the Parts/Calculations lists), ``review`` over the whole value (the
# mechanism plus every presentation field: labels carried inside the PQL,
# capabilityDelta, why, inspection, verification, decisions, limits, and, for a
# set-shaped value, its candidates list). A label change is a ``review``-only
# change; a binding change touches the PQL and so touches both.


def _pnc_source(value: Mapping[str, Any]) -> dict[str, Any]:
    pql = value.get("PQL") or {}
    return {
        "PQL": {"Ticks": pql.get("Ticks", [])},
        "existingParts": value.get("existingParts", []),
        "proposedParts": value.get("proposedParts", []),
        "existingCalculations": value.get("existingCalculations", []),
        "proposedCalculations": value.get("proposedCalculations", []),
    }


def add_digests(value: dict[str, Any]) -> dict[str, Any]:
    """Set ``pnc`` and ``review`` on ``value`` (mutated in place, and returned).

    Idempotent: any ``pnc``/``review`` already on ``value`` are dropped before
    either is computed, so calling this twice on the same dict recomputes the
    same two digests rather than digesting its own previous answer.
    """
    value.pop("pnc", None)
    value.pop("review", None)
    value["pnc"] = _digest_of(_pnc_source(value))
    value["review"] = _digest_of(value)
    return value


# --------------------------------------------------------------------------- partness (task 75)
#
# "A Part computed from a part is a part": a part is any address under
# ``proposal.*`` or ``px.exp.*`` -- the two mounts a composition proposal and its
# staged outputs live under (``ADDRESS_PREFIX`` above is one ``proposal.``
# spelling; ``px.exp.`` is where ``crisp import`` writes what a PQL produces,
# see the fixture's ``into`` addresses). Force mode no longer refuses a ``with``
# binding to one: it accepts it, and the proposal's own transitive basis --
# every root part address that binding traces back to -- is recorded rather than
# thrown away, so ``px`` can show the same propagation once the run happens
# (``pyto/src/pyto/px.py`` ``part_basis``, the same rule over a run record).


def is_part(address: str) -> bool:
    return address.startswith("proposal.") or address.startswith("px.exp.")


def _document_basis(document: Mapping[str, Any], store: Mapping[str, Any]) -> dict[str, set[str]]:
    """address -> the part addresses (``is_part``) it stands on, transitively --
    crisp's own mirror of ``px.part_basis``, computed from a PQL document and a
    store before anything has actually run. A store address that is itself a
    part seeds its own basis; a Calculation's declared outputs (``into``)
    inherit the union of whatever its ``with`` bindings stand on, plus
    themselves when an output address is itself under a part mount."""
    basis: dict[str, set[str]] = {}
    for address in store:
        if is_part(address):
            basis[address] = {address}
    for tick in document.get("Ticks", []):
        for entry in tick.get("Calculations", []):
            combined: set[str] = set()
            for _name, address in (entry.get("with") or {}).items():
                for one in _addresses(address):
                    if not isinstance(one, str):
                        continue
                    combined |= basis.get(one, set())
                    if is_part(one):
                        combined.add(one)
            for produced in _addresses(entry.get("into")):
                total = combined | ({produced} if is_part(produced) else set())
                if total:
                    basis[produced] = basis.get(produced, set()) | total
    return basis


# --------------------------------------------------------------------------- live or pinned bindings (task 75)
#
# A ``with`` value is either a bare address (live: whatever the store holds
# now) or ``{"address": ..., "sha256": ...}`` (pinned: refuse unless the store's
# current value digests to exactly that, task 75 item 3). The proposal's own
# ``PQL`` field always stays plain addresses -- the grammar the studio reads has
# no third shape for ``with`` -- so ``_normalize_pql`` strips every pin out to a
# side table (``pins``) keyed by address, beside ``PQL``, once at template time.


def _binding_address(value: Any) -> Any:
    if isinstance(value, MappingABC):
        return value.get("address")
    return value


def _binding_pin(value: Any) -> str | None:
    if isinstance(value, MappingABC):
        return value.get("sha256")
    return None


def _normalize_pql(document: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """``document`` with every ``with`` value reduced to a plain address, and every
    pin it carried collected into a flat ``address -> sha256`` table."""
    normalized = copy.deepcopy(dict(document))
    pins: dict[str, str] = {}
    for tick in normalized.get("Ticks", []):
        for entry in tick.get("Calculations", []):
            with_ = entry.get("with") or {}
            plain: dict[str, Any] = {}
            for name, binding in with_.items():
                if isinstance(binding, (list, tuple)):
                    plain[name] = [_binding_address(one) for one in binding]
                    for one in binding:
                        pin = _binding_pin(one)
                        if pin is not None:
                            pins[_binding_address(one)] = pin
                    continue
                address = _binding_address(binding)
                pin = _binding_pin(binding)
                if pin is not None:
                    pins[address] = pin
                plain[name] = address
            entry["with"] = plain
    return normalized, pins


def _check_pins(pins: Mapping[str, str], store: Mapping[str, Any]) -> None:
    """Refuse by name the first pinned address whose store value does not digest
    to what the pin names (the pin may be a full sha256 or a short prefix of one,
    like the revision a proposal's own address carries)."""
    for address in sorted(pins):
        pin = pins[address]
        if address not in store:
            raise CrispRefusal(f"pinned {address} is not in the store (expected {pin[:12]})")
        actual = _digest_of(store[address])
        if not (actual == pin or actual.startswith(pin)):
            raise CrispRefusal(f"pinned {address} expected {pin[:12]} got {actual[:12]}")


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


def _address_for(set_name: str, option: str, value: dict[str, Any]) -> tuple[str, str]:
    """``proposal.neat.composition.<set>.<option>.<revision>``, revision the first 12
    hex of ``review`` -- the whole value's digest, task 75 item 1 -- computed (and
    set, along with ``pnc``) on ``value`` here, since every addressed value needs
    both before it is written."""
    add_digests(value)
    address = f"{ADDRESS_PREFIX}{set_name}.{option}.{value['review'][:12]}"
    return address, value["review"]


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
) -> tuple[list, list, list]:
    """Force-mode validation: refuses the first "with" binding or "call" that does
    not resolve, naming it, and any backwards read -- except a binding to a part
    (``is_part``, task 75): that is never refused, and every part address any
    binding in this document stands on (transitively, ``_document_basis``) is
    collected instead. Returns (existingParts, existingCalculations, basis) on
    success -- proposedParts/proposedCalculations are always empty here, because
    anything else that would need one is a refusal instead."""
    _refuse_backwards_reads(document)
    existing_parts: dict[str, Any] = {}
    existing_calcs: dict[str, Any] = {}
    basis: set[str] = set()
    doc_basis = _document_basis(document, store)
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
                        basis |= doc_basis.get(one, set())
                    elif one in produced_before_this_tick or one in seen:
                        basis |= doc_basis.get(one, set())
                    elif is_part(one):
                        # Partness propagates instead of refusing: a binding to a part --
                        # store address or not -- is accepted and recorded as basis, never
                        # refused. Production is gated at promotion, never at binding.
                        basis.add(one)
                        basis |= doc_basis.get(one, set())
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
        sorted(basis),
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
        "basis": [],
        "provisional": False,
    }
    value.update(_placeholder_prose(mode))
    add_digests(value)
    return value


def build_pql_proposal(
    sentence: str, document: Mapping[str, Any], store: Mapping[str, Any], registry: Mapping[str, Any], mode: str
) -> dict[str, Any]:
    # A pin is verified at import, never here (task 75 item 3): "import resolves
    # a pinned binding ... and refuses by name" -- template only has to accept the
    # syntax and carry it forward, so a proposal can be written (and inspected)
    # even when its pin no longer matches; import is the one door into the store.
    document, pins = _normalize_pql(document)
    if mode == "force":
        existing_parts, existing_calcs, basis = check_pql_force(document, store, registry)
        proposed_parts: list = []
        proposed_calcs: list = []
    else:
        existing_parts, proposed_parts, existing_calcs, proposed_calcs = classify_pql_imply(
            document, store, registry
        )
        basis = []
    value: dict[str, Any] = {
        "capabilityDelta": sentence,
        "why": f"a PQL document handed to `crisp template` in {mode} mode: {sentence!r}",
        "existingParts": existing_parts,
        "proposedParts": proposed_parts,
        "existingCalculations": existing_calcs,
        "proposedCalculations": proposed_calcs,
        "PQL": document,
        "basis": basis,
        "provisional": bool(basis),
    }
    if pins:
        value["pins"] = pins
    value.update(_placeholder_prose(mode))
    if mode == "force":
        slot = find_slot(value)
        if slot:
            raise CrispRefusal(f"proposal has an unresolved slot at {slot}")
    add_digests(value)
    return value


# --------------------------------------------------------------------------- A-Star intake (task 75)


ASTAR_RESERVED = ("known", "unresolved", "references", "possibilities", "return_when")


def build_astar_proposal(
    sentence: str,
    study: Mapping[str, Any],
    store: Mapping[str, Any],
    registry: Mapping[str, Any],
    set_name: str,
    mode: str,
) -> dict[str, Any]:
    """An A-Star study's ``known``/``unresolved``/``return_when`` seeding a proposal:
    a ``known`` entry that names a store or registry address becomes an
    existingPart/existingCalculation; each ``unresolved`` entry becomes a
    "{?} <text>" slot in ``decisions``; ``return_when`` becomes ``limits``.
    Nothing here writes a PQL invocation -- an A-Star study says what is known
    and what is not, not how to wire a Calculation -- so a fully-resolved study
    (no ``unresolved`` left) carries no "{?}" anywhere and force mode accepts
    it; one that still has an unresolved entry refuses in force mode, on the
    same backstop scan every other proposal shape refuses through
    (``find_slot``). Any field the local PoC shape carries beyond the five this
    reads is kept, unread, under ``astar_extra``."""
    known = study.get("known") or {}
    if isinstance(known, MappingABC):
        named = list(known.items())
    else:
        named = [(str(a), a) for a in known]

    existing_parts: dict[str, Any] = {}
    existing_calcs: dict[str, Any] = {}
    for _name, address in named:
        if not isinstance(address, str):
            continue
        if address in store:
            existing_parts.setdefault(address, _existing_part_entry(address, store))
        elif address in registry:
            existing_calcs.setdefault(address, _existing_calc_entry(address, registry))

    unresolved = list(study.get("unresolved") or [])
    decisions = (
        [f"{SLOT} {text}" for text in unresolved] if unresolved else _placeholder_prose(mode)["decisions"]
    )
    return_when = study.get("return_when")
    limits = [str(return_when)] if return_when else _placeholder_prose(mode)["limits"]

    extra = {k: v for k, v in study.items() if k not in ASTAR_RESERVED}

    value: dict[str, Any] = {
        "capabilityDelta": sentence,
        "why": f"an A-Star study handed to `crisp template` in {mode} mode: {sentence!r}",
        "existingParts": [existing_parts[a] for a in sorted(existing_parts)],
        "proposedParts": [],
        "existingCalculations": [existing_calcs[a] for a in sorted(existing_calcs)],
        "proposedCalculations": [],
        "PQL": {"Ticks": [{"name": set_name, "Calculations": []}]},
        "basis": [],
        "provisional": False,
        "inspection": _placeholder_prose(mode)["inspection"],
        "verification": _placeholder_prose(mode)["verification"],
        "decisions": decisions,
        "limits": limits,
    }
    if extra:
        value["astar_extra"] = extra
    if mode == "force":
        slot = find_slot(value)
        if slot:
            raise CrispRefusal(f"proposal has an unresolved slot at {slot}")
    add_digests(value)
    return value


def _unwrap_part(document: Mapping[str, Any]) -> Mapping[str, Any]:
    """A Part's ``value``, when ``document`` is one (carries ``address``/``value``/
    ``sha256``); ``document`` itself otherwise -- an A-Star study may be handed
    either bare or wrapped."""
    if isinstance(document, MappingABC) and {"address", "value", "sha256"} <= set(document):
        return document["value"]
    return document


def cmd_template(args: argparse.Namespace) -> int:
    store = _load_json(args.store)
    registry = _load_registry(args.registry)

    if args.astar:
        study = _unwrap_part(_load_json(args.astar))
        value = build_astar_proposal(args.sentence, study, store, registry, args.set_name, args.mode)
    elif args.pql:
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
    name, then the alternate address. Yields the address replaced too, so a
    caller holding a pin on it (task 75 item 3) can carry the pin forward onto
    the new address rather than losing it."""
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
                    yield candidate, change, mutated, address


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

    base_pins: dict[str, str] = dict(base_value.get("pins") or {})

    options: list[tuple[str, str, dict, str | None, str | None]] = []
    if do_bindings:
        for index, (candidate, change, mutated, source) in enumerate(_binding_options(pql, store), start=1):
            options.append((f"a{index}-{_slug_of(candidate)}", change, mutated, source, candidate))
    if do_calcs:
        for index, (candidate, change, mutated) in enumerate(
            _calculation_options(pql, registry, store), start=1
        ):
            options.append((f"b{index}-{_slug_of(candidate)}", change, mutated, None, None))

    cut = 0
    if args.max is not None and len(options) > args.max:
        cut = len(options) - args.max
        options = options[: args.max]

    out_dir = os.path.dirname(os.path.abspath(args.proposal))
    for slug, change, mutated, source_address, candidate_address in options:
        existing_parts, proposed_parts, existing_calcs, proposed_calcs = classify_pql_imply(
            mutated, store, registry
        )
        value = dict(base_value)
        pins = dict(base_pins)
        # A pinned binding stays pinned when Variation A substitutes its address: the
        # pin moves to the candidate, re-digested from the store it now points at
        # (task 75 item 3) -- never a stale pin against a binding that changed.
        if source_address is not None and source_address in pins:
            del pins[source_address]
            if candidate_address in store:
                pins[candidate_address] = _digest_of(store[candidate_address])
        value.update(
            {
                "existingParts": existing_parts,
                "proposedParts": proposed_parts,
                "existingCalculations": existing_calcs,
                "proposedCalculations": proposed_calcs,
                "PQL": mutated,
                "whatChanged": change,
            }
        )
        if pins:
            value["pins"] = pins
        else:
            value.pop("pins", None)
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
    _check_pins(value.get("pins") or {}, store)

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


# --------------------------------------------------------------------------- cards (task 75)
#
# "crisp cards" reads a proposal (or the whole set directory `crisp template`
# then `crisp vary` wrote into together) and emits one Blok card set Part:
# ``proposal.neat.cards.<set>.<revision>``, ``cards`` = [root labelled, root
# unlabelled, then every option found], each card carrying both digests, the
# PQL, its bindings' exact store values, and (for a variant) the one-line
# "what changed" `crisp vary` already prints but did not, until now, keep.

CARDS_ADDRESS_PREFIX = "proposal.neat.cards."


def _option_of(address: str) -> str:
    tail = address[len(ADDRESS_PREFIX):]
    _set_name, option, _revision = tail.rsplit(".", 2)
    return option


def _variant_sort_key(option: str) -> tuple[Any, ...]:
    match = re.match(r"^([a-z]+)(\d+)-", option)
    if match:
        return (0, match.group(1), int(match.group(2)), option)
    return (1, option)


def _discover_set(path: str) -> tuple[str, dict[str, dict[str, Any]]]:
    """(set_name, {option: proposal document, ...}) for every proposal Part of
    one set found under ``path`` -- a single ``proposal.json``, or the
    directory it (and `crisp vary`'s options) live in. Two passes, since the
    set a bare directory names is only known once its "root" file is found
    among however ``os.listdir`` happens to order the files (a1 sorts before
    root)."""
    is_dir = os.path.isdir(path)
    directory = path if is_dir else (os.path.dirname(os.path.abspath(path)) or ".")

    documents: list[dict[str, Any]] = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        try:
            document = _load_json(os.path.join(directory, name))
        except (OSError, ValueError):
            continue
        address = document.get("address") if isinstance(document, MappingABC) else None
        if isinstance(address, str) and address.startswith(ADDRESS_PREFIX):
            documents.append(document)

    if is_dir:
        set_name = next(
            (_set_of(d["address"]) for d in documents if _option_of(d["address"]) == "root"), None
        )
    else:
        set_name = _set_of(_load_json(path)["address"])

    by_option: dict[str, dict[str, Any]] = {}
    for document in documents:
        if _set_of(document["address"]) == set_name:
            by_option[_option_of(document["address"])] = document

    if set_name is None or "root" not in by_option:
        raise CrispRefusal(f"crisp cards: no root proposal for a set found under {path!r}")
    return set_name, by_option


def _card_bindings(document: Mapping[str, Any], store: Mapping[str, Any]) -> dict[str, Any]:
    """Every address any "with" binding in ``document`` names, resolved to its
    exact current value in ``store`` -- "the exact input values from the store
    for its bindings" (task 75 item 2). An address the store does not hold is
    left out: a card shows what it can verify, nothing guessed."""
    out: dict[str, Any] = {}
    for tick in document.get("Ticks", []):
        for entry in tick.get("Calculations", []):
            for _name, address in (entry.get("with") or {}).items():
                if isinstance(address, str) and address in store and address not in out:
                    out[address] = store[address]
    return {address: out[address] for address in sorted(out)}


def _card_from_proposal(
    document: Mapping[str, Any],
    store: Mapping[str, Any],
    *,
    labels: list[str],
    what_changed: str,
) -> dict[str, Any]:
    value = document["value"]
    pql = value.get("PQL") or {}
    card: dict[str, Any] = {
        "capabilityDelta": value.get("capabilityDelta"),
        "why": value.get("why"),
        "existingParts": value.get("existingParts", []),
        "proposedParts": value.get("proposedParts", []),
        "existingCalculations": value.get("existingCalculations", []),
        "proposedCalculations": value.get("proposedCalculations", []),
        "PQL": pql,
        "inspection": value.get("inspection", []),
        "verification": value.get("verification", []),
        "decisions": value.get("decisions", []),
        "limits": value.get("limits", []),
        "labels": list(labels),
        "bindings": _card_bindings(pql, store),
        "whatChanged": what_changed,
    }
    add_digests(card)
    card["sourceAddress"] = document["address"]
    return card


def build_cards(
    set_name: str, by_option: Mapping[str, dict[str, Any]], store: Mapping[str, Any], label: str | None
) -> dict[str, Any]:
    """The cards list, in order: root labelled, root unlabelled -- identical
    structure but for the label, so ``pnc`` (Parts and Calculations only) is the
    same for both and ``review`` (the whole card, label included) is not -- then
    every other option present, sorted a1, a2, ..., b1, b2, ... ."""
    root = by_option["root"]
    labels = [label] if label else []
    cards = [
        _card_from_proposal(root, store, labels=labels, what_changed=""),
        _card_from_proposal(root, store, labels=[], what_changed=""),
    ]
    for option in sorted((o for o in by_option if o != "root"), key=_variant_sort_key):
        document = by_option[option]
        what_changed = document["value"].get("whatChanged", "")
        cards.append(_card_from_proposal(document, store, labels=[], what_changed=what_changed))
    return {"cards": cards}


CARDS_CSS = """
:root{--paper:#F5F7F4;--ink:#1B2630;--muted:#5B6A75;--rule:#D3DADD;--panel:#ECEFEC;--accent:#2F6F4E}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#141A1F;--ink:#E6EAEC;--muted:#9AA7B0;--rule:#2B353D;--panel:#1C242B;--accent:#6FBF8F}}
:root[data-theme="dark"]{--paper:#141A1F;--ink:#E6EAEC;--muted:#9AA7B0;--rule:#2B353D;--panel:#1C242B;--accent:#6FBF8F}
body{background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.5;margin:0;padding:24px 18px 64px}
main{max-width:1040px;margin:0 auto}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
h1{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:clamp(28px,5vw,38px);margin:0 0 18px}
.deck{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.card{border:1px solid var(--rule);background:var(--panel);padding:16px 18px}
.card h2{font-family:"Fraunces",Georgia,serif;font-size:18px;margin:0 0 6px}
.tag{display:inline-block;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;letter-spacing:.05em;text-transform:uppercase;border:1px solid var(--accent);color:var(--accent);padding:1px 7px;margin:0 6px 6px 0}
.digest{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--muted);word-break:break-all;margin:2px 0}
.changed{font-size:13px;font-style:italic;color:var(--muted);margin:8px 0}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}
td{padding:2px 6px 2px 0;vertical-align:top;font-family:"IBM Plex Mono",ui-monospace,monospace}
td.k{color:var(--muted);white-space:nowrap}
pre{background:var(--paper);border:1px solid var(--rule);padding:8px 10px;overflow-x:auto;font-size:12px;margin:6px 0}
footer{margin-top:26px;font-size:13px;color:var(--muted);border-top:1px solid var(--rule);padding-top:10px}
"""


def _card_html(card: Mapping[str, Any]) -> str:
    labels = card.get("labels") or []
    heading = ", ".join(labels) if labels else "(unlabelled)"
    tags = "".join(f'<span class="tag">{html.escape(text)}</span>' for text in labels) or (
        '<span class="tag">unlabelled</span>'
    )
    changed = (
        f'<p class="changed">what changed: {html.escape(str(card["whatChanged"]))}</p>'
        if card.get("whatChanged")
        else ""
    )
    bindings_rows = "".join(
        f"<tr><td class='k'>{html.escape(address)}</td><td>{html.escape(json.dumps(value))}</td></tr>"
        for address, value in (card.get("bindings") or {}).items()
    ) or "<tr><td colspan='2'>-</td></tr>"
    pql_text = html.escape(json.dumps(card.get("PQL"), indent=2, sort_keys=True))
    return f"""<article class="card">
<h2>{html.escape(heading)}</h2>
{tags}
<p class="digest">pnc: {card['pnc']}</p>
<p class="digest">review: {card['review']}</p>
{changed}
<table>{bindings_rows}</table>
<pre><code>{pql_text}</code></pre>
</article>"""


def render_cards_html(set_name: str, cards_value: Mapping[str, Any]) -> str:
    """A static page in the owner's Blok style: one card per candidate, both
    digests on each, no script anywhere. "Approve must identify the exact
    candidate": its pnc, never its label."""
    body = "\n".join(_card_html(card) for card in cards_value.get("cards", []))
    return f"""<title>{html.escape(set_name)} cards</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CARDS_CSS}</style>
<main>
<p class="eyebrow">crisp cards &middot; set {html.escape(set_name)} &middot; review {cards_value['review'][:12]}</p>
<h1>{html.escape(set_name)}</h1>
<div class="deck">
{body}
</div>
<footer>Approve must identify the exact candidate: its pnc, not its label. pnc is the Parts and
Calculations alone; review is the whole card, labels included -- a label changes review and
never pnc.</footer>
</main>
"""


def cmd_cards(args: argparse.Namespace) -> int:
    store = _load_json(args.store)
    set_name, by_option = _discover_set(args.path)
    cards_value = build_cards(set_name, by_option, store, args.labels)
    add_digests(cards_value)
    address = f"{CARDS_ADDRESS_PREFIX}{set_name}.{cards_value['review'][:12]}"

    directory = args.path if os.path.isdir(args.path) else (os.path.dirname(os.path.abspath(args.path)) or ".")
    out_path = args.out or os.path.join(directory, "cards.json")
    _write_part(address, cards_value, out_path)

    html_path = os.path.splitext(out_path)[0] + ".html"
    with open(html_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_cards_html(set_name, cards_value))

    print(f"address: {address}")
    print(f"wrote:   {_rel(out_path)}")
    print(f"html:    {_rel(html_path)}")
    for card in cards_value["cards"]:
        label = ",".join(card["labels"]) if card["labels"] else "(unlabelled)"
        print(f"  {label}  pnc={card['pnc'][:12]}  review={card['review'][:12]}")
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
    template.add_argument(
        "--astar", default=None,
        help="an A-Star study Part JSON: known/unresolved/references/possibilities/return_when",
    )
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

    cards = sub.add_parser("cards", help="emit a Blok card set: root labelled, root unlabelled, each variant")
    cards.add_argument("path", help="a proposal.json, or the set directory `crisp template`/`crisp vary` wrote into")
    cards.add_argument("--store", required=True)
    cards.add_argument("--labels", default=None, help="the label attached to the root labelled card")
    cards.add_argument("--out", default=None, help="where to write the cards Part (default: cards.json beside path)")

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
        if args.command == "cards":
            return cmd_cards(args)
    except CrispRefusal as refused:
        print(f"crisp: {refused}", file=sys.stderr)
        return 1
    raise AssertionError(f"unreachable: unknown command {args.command!r}")  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
