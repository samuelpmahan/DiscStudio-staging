"""Retain a PCR program as declarative data and rebuild it through an explicit registry.

Experiment-local (nothing here is in pyto/src). The retained record is data only:
it never contains a callable, a lambda, a pickle or a source string, and it never
claims to contain executable Python (docs/PYTHON-LAB-STEWARDSHIP.md:39). Replay
means `from_program(record["program"], REGISTRY)` -> PCR, i.e. rebuilding the
program from data and resolving every `fn.` address against functions the replay
process imported itself.

Shapes
------
program  {"name": str,
          "ticks": [{"name": str,
                     "calculations": [{"id": str,
                                       "calculation": "fn.<address>",
                                       "inputs": {name: "px:<address>" | "fn:<id>"},
                                       "args": {...},
                                       "into": "<address>" | None}]}]}

The calculation entries are byte-identical to the entries of
`dataclasses.asdict(TickTestimony)` (pcr.py:59-75), which is why the testimony
shape wins the candidates/ comparison: no translation layer sits between what a
run testifies and what is retained.

record   {"program": program,
          "external": {address: <json value> | {"digest": sha256, "ref": "<sidecar file>"}},
          "provider": {"pyto": {...}, "registry": {address: {"module", "source_sha256"}}},
          "results": {invocation id: sha256 | None}}

Rules this module enforces
--------------------------
* Shadow rule (LAB transfer ledger, "Shadow rejection"; src/core/exec.js:45 and
  :58): an `args` key equal to a bound input name is refused **at export**,
  naming the invocation. pyto lets args win silently (pcr.py:159-160), so a
  retained program carrying such a key would replay a value the testimony does
  not explain. Refusing at export leaves pcr.py untouched ({?} ShadowRule).
* `graph.Pcr.to_pcr_dict()` output is refused by `from_program`: Pcr does not
  execute (graph.py:29-31) and PCR/Pcr must not be presented as one round-trip
  format (docs/PYTHON-LAB-STEWARDSHIP.md:19).
* A calculation address missing from the registry raises KeyError naming the
  address before any PCR is built and therefore before any execution.
* Digests are sha256 over `json.dumps(value, sort_keys=True, separators=(",", ":"))`
  with **no** `default=` (critic gap 10): a value JSON cannot describe gets
  `None`, never a digest of its repr.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import importlib.metadata
import inspect
import json
import os
from typing import Any, Iterable, Mapping

import pyto
from pyto import PCR, Part, PcrRun, PxC
from pyto.pcr import Invocation, ResultRef  # pyto/__init__.py:1-23 omits Invocation

PX = "px:"
FN = "fn:"
# PCR.calc takes these as keyword-only parameters (pcr.py:88-96), so an input
# named like one of them cannot be rebuilt through **inputs.
RESERVED_INPUT_NAMES = ("id", "into", "args")
PROVIDER_MODULES = ("core.py", "pcr.py")


class RetainError(ValueError):
    """The program or the run cannot be retained as honest declarative data."""


class ShadowedInputError(RetainError):
    """An args key shadows a bound input (src/core/exec.js:45, :58)."""


class NotAProgramError(RetainError):
    """The dict is a graph.Pcr projection, not a PCR program (stewardship:19)."""


# --------------------------------------------------------------------------- digests


def canonical_json(value: Any) -> str:
    """Canonical JSON text, or raise. No default=: an undescribable value must fail."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest_of(value: Any) -> str | None:
    """sha256 of the canonical JSON, or None when JSON cannot describe the value."""
    try:
        text = canonical_json(value)
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_jsonable(value: Any) -> bool:
    try:
        canonical_json(value)
    except (TypeError, ValueError):
        return False
    return True


# ------------------------------------------------------------------- program export


def _check_shadow(invocation_id: str, input_names: Iterable[str], args: Mapping[str, Any]) -> None:
    shadowed = sorted(name for name in input_names if name in args)
    if shadowed:
        raise ShadowedInputError(
            f"retain: invocation '{invocation_id}' has args {shadowed} shadowing bound "
            f"input(s) of the same name; pyto would let args win silently "
            f"(pcr.py:159-160) while the LAB fails loud (src/core/exec.js:45, :58), "
            f"so the program is refused at export"
        )


def _check_reserved(invocation_id: str, input_names: Iterable[str]) -> None:
    clashing = sorted(name for name in input_names if name in RESERVED_INPUT_NAMES)
    if clashing:
        raise RetainError(
            f"retain: invocation '{invocation_id}' binds input(s) {clashing}, which are "
            f"keyword-only parameters of PCR.calc (pcr.py:88-96) and could not be "
            f"rebuilt from the retained program"
        )


def _check_args_jsonable(invocation_id: str, args: Mapping[str, Any]) -> None:
    for key, value in args.items():
        if not is_jsonable(value):
            raise RetainError(
                f"retain: invocation '{invocation_id}' arg '{key}' is a "
                f"{type(value).__name__}, which JSON cannot describe; retained data "
                f"holds no executable code and no repr placeholders (docs/PYTHON-LAB-STEWARDSHIP.md:39)"
            )


def _entry_from_invocation(invocation: Invocation) -> dict[str, Any]:
    inputs: dict[str, str] = {}
    for name, binding in invocation.bindings.items():
        source = binding.source
        if isinstance(source, Part):
            inputs[name] = f"{PX}{source.address}"
        elif isinstance(source, ResultRef):
            inputs[name] = f"{FN}{source.calculation_id}"
        else:
            raise RetainError(
                f"retain: invocation '{invocation.id}' input '{name}' is bound to a "
                f"{type(source).__name__}; only Part and ResultRef are retainable "
                f"(pcr.py:147-157)"
            )
    _check_reserved(invocation.id, inputs)
    _check_shadow(invocation.id, inputs, invocation.args)
    _check_args_jsonable(invocation.id, invocation.args)
    return {
        "id": invocation.id,
        "calculation": invocation.calculation.address,
        "inputs": inputs,
        "args": dict(invocation.args),
        "into": invocation.into.address if invocation.into is not None else None,
    }


def _entry_from_testimony(testimony: Any) -> dict[str, Any]:
    entry = dataclasses.asdict(testimony)
    _check_reserved(entry["id"], entry["inputs"])
    _check_shadow(entry["id"], entry["inputs"], entry["args"])
    _check_args_jsonable(entry["id"], entry["args"])
    for name, ref in entry["inputs"].items():
        if not (ref.startswith(PX) or ref.startswith(FN)):
            raise RetainError(
                f"retain: invocation '{entry['id']}' input '{name}' has ref '{ref}', "
                f"which is neither 'px:<address>' nor 'fn:<id>'"
            )
    return entry


def to_program(source: PCR | PcrRun) -> dict[str, Any]:
    """Export a PCR (authoring) or a PcrRun (testimony) as the retained program dict.

    Both walk `source.ticks[*].calculations[*]`; a PcrRun's entries are already
    the retained entry shape, so `to_program(run)["ticks"] == asdict(run.ticks)`.
    """
    if isinstance(source, PCR):
        name = source.name
        ticks = [
            {"name": tick.name, "calculations": [_entry_from_invocation(i) for i in tick.calculations]}
            for tick in source.ticks
        ]
    elif isinstance(source, PcrRun):
        name = source.pcr
        ticks = [
            {"name": tick.name, "calculations": [_entry_from_testimony(c) for c in tick.calculations]}
            for tick in source.ticks
        ]
    else:
        raise TypeError(f"retain.to_program: expected a PCR or a PcrRun, got {type(source).__name__}")
    return {"name": name, "ticks": ticks}


# ------------------------------------------------------------------- program import


def _reject_pcr_projection(program: Any) -> None:
    if isinstance(program, Mapping) and ("PrincipleComponentRender" in program or "Ticks" in program):
        raise NotAProgramError(
            "retain.from_program: this is a graph.Pcr projection "
            "(PrincipleComponentRender/Ticks), not a PCR program. Pcr deliberately does "
            "not execute (graph.py:29-31) and the two classes must not be presented as "
            "one round-trip format (docs/PYTHON-LAB-STEWARDSHIP.md:19)"
        )


def _walk_entries(program: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    if not isinstance(program, Mapping):
        raise NotAProgramError(f"retain.from_program: expected a mapping, got {type(program).__name__}")
    _reject_pcr_projection(program)
    if not isinstance(program.get("name"), str) or not program["name"]:
        raise NotAProgramError("retain.from_program: program['name'] must be a nonempty string")
    ticks = program.get("ticks")
    if not isinstance(ticks, list):
        raise NotAProgramError("retain.from_program: program['ticks'] must be a list")
    out: list[tuple[str, Mapping[str, Any]]] = []
    for index, tick in enumerate(ticks):
        if not isinstance(tick, Mapping) or not isinstance(tick.get("name"), str) or not tick["name"]:
            raise NotAProgramError(f"retain.from_program: ticks[{index}] needs a nonempty 'name'")
        calculations = tick.get("calculations")
        if not isinstance(calculations, list):
            raise NotAProgramError(f"retain.from_program: ticks[{index}]['calculations'] must be a list")
        for entry in calculations:
            if not isinstance(entry, Mapping):
                raise NotAProgramError(f"retain.from_program: {tick['name']} holds a non-mapping calculation")
            out.append((tick["name"], entry))
    return out


def from_program(program: Mapping[str, Any], registry: Mapping[str, Any]) -> PCR:
    """Rebuild a PCR through PCR.calc so writer/id rules re-apply (pcr.py:99-133).

    Every calculation address is resolved against `registry` *before* the PCR is
    built, so a registry hole raises KeyError naming the address and nothing runs.
    """
    entries = _walk_entries(program)
    missing = sorted({entry.get("calculation") for _, entry in entries} - set(registry))
    if missing:
        raise KeyError(
            f"retain.from_program: registry has no Calculation for {missing}; "
            f"registry holds {sorted(registry)}"
        )

    pcr = PCR(program["name"])
    for tick_name, entry in entries:
        invocation_id = entry.get("id")
        if not isinstance(invocation_id, str) or not invocation_id:
            raise NotAProgramError(f"retain.from_program: {tick_name} holds a calculation without an 'id'")
        inputs_spec = entry.get("inputs") or {}
        args = dict(entry.get("args") or {})
        _check_reserved(invocation_id, inputs_spec)
        _check_shadow(invocation_id, inputs_spec, args)
        inputs: dict[str, Any] = {}
        for name, ref in inputs_spec.items():
            if not isinstance(ref, str):
                raise NotAProgramError(f"retain.from_program: '{invocation_id}' input '{name}' must be a string")
            if ref.startswith(PX):
                inputs[name] = Part(ref[len(PX):])
            elif ref.startswith(FN):
                inputs[name] = ResultRef(ref[len(FN):])
            else:
                raise NotAProgramError(
                    f"retain.from_program: '{invocation_id}' input '{name}' has ref '{ref}'; "
                    f"expected 'px:<address>' or 'fn:<id>'"
                )
        pcr.calc(
            tick_name,
            registry[entry["calculation"]],
            id=invocation_id,
            into=entry.get("into"),
            args=args,
            **inputs,
        )
    return pcr


def registry_from_pcr(pcr: PCR) -> dict[str, Any]:
    """The Calculations a PCR actually invokes, keyed by address (for provider identity)."""
    return {
        invocation.calculation.address: invocation.calculation
        for tick in pcr.ticks
        for invocation in tick.calculations
    }


# ------------------------------------------------------------------ sidecar encoding


def _sortable(pair: tuple[Any, Any]) -> str:
    return canonical_json(pair[0])


def describe(value: Any, where: str) -> Any:
    """A JSON-safe, deterministic description of a value JSON alone cannot hold.

    Type-tagged and lossless enough to digest; it is a description, not a value,
    and it never falls back to repr() (a default repr carries a process-dependent
    address, which would show up as pyto-caused digest drift, critic gap 10).
    """
    if callable(value) or inspect.ismodule(value):
        raise RetainError(
            f"retain: {where} holds a {type(value).__name__}; retained data never holds "
            f"executable code (docs/PYTHON-LAB-STEWARDSHIP.md:39)"
        )
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (bytes, bytearray)):
        return {"$bytes": bytes(value).hex()}
    if isinstance(value, datetime.datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, datetime.date):
        return {"$date": value.isoformat()}
    if isinstance(value, list):
        return [describe(item, f"{where}[{i}]") for i, item in enumerate(value)]
    if isinstance(value, tuple):
        return {"$tuple": [describe(item, f"{where}[{i}]") for i, item in enumerate(value)]}
    if isinstance(value, (set, frozenset)):
        kind = "$set" if isinstance(value, set) else "$frozenset"
        items = [describe(item, f"{where}{{}}") for item in value]
        return {kind: sorted(items, key=canonical_json)}
    if isinstance(value, Mapping):
        pairs = [
            [describe(key, f"{where}.<key>"), describe(item, f"{where}[{key!s}]")]
            for key, item in value.items()
        ]
        return {"$dict": sorted(pairs, key=_sortable)}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        cls = type(value)
        return {
            "$dataclass": f"{cls.__module__}.{cls.__qualname__}",
            "fields": {
                field.name: describe(getattr(value, field.name), f"{where}.{field.name}")
                for field in dataclasses.fields(value)
            },
        }
    raise RetainError(
        f"retain: {where} holds a {type(value).__name__}, which cannot be described as "
        f"data without falling back to repr(); describe it explicitly or exclude it"
    )


def _safe_name(address: str) -> str:
    return "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in address)


# ------------------------------------------------------------------------- provider


def _sha256_path(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _module_source_sha256(obj: Any) -> tuple[str | None, str | None]:
    """(module name, sha256 of the module's source file) for a Calculation's callable."""
    target = getattr(obj, "calculate", obj)
    module = inspect.getmodule(target)
    path = inspect.getsourcefile(target) if module is None else inspect.getsourcefile(module)
    name = None if module is None else module.__name__
    return name, (_sha256_path(path) if path and os.path.exists(path) else None)


def provider_identity(registry: Mapping[str, Any]) -> dict[str, Any]:
    """Pyto distribution version, library module hashes, and per-address provider hashes.

    This is the identity a replay compares against before trusting a record
    (docs/PYTHON-LAB-STEWARDSHIP.md:37).
    """
    library_dir = os.path.dirname(os.path.abspath(pyto.core.__file__))
    modules = {}
    for name in PROVIDER_MODULES:
        path = os.path.join(library_dir, name)
        modules[name] = _sha256_path(path) if os.path.exists(path) else None
    try:
        version = importlib.metadata.version("pyto-lab")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover - install always present here
        version = None
    calculations = {}
    for address in sorted(registry):
        module_name, source_sha = _module_source_sha256(registry[address])
        calculations[address] = {"module": module_name, "source_sha256": source_sha}
    return {
        "pyto": {"package": "pyto-lab", "version": version, "modules": modules},
        "registry": calculations,
    }


# -------------------------------------------------------------------------- retain


def retain_run(
    pxc: PxC,
    run: PcrRun,
    external_addresses: Iterable[str],
    *,
    registry: Mapping[str, Any],
    record_path: str | None = None,
) -> dict[str, Any]:
    """Retain a finished run as a replayable record.

    `registry` is required (the plan writes `retain_run(pxc, run, external_addresses)`):
    a PcrRun names calculation addresses only, so provider identity — the thing a
    replay checks before trusting the record — cannot be derived from the run.
    `registry_from_pcr(pcr)` builds it from the program that ran.

    Non-JSON external values are written next to `record_path` as
    `<stem>.external.<address>.json` and referenced as {"digest", "ref"}; without a
    `record_path` there is nowhere to put them and the call is refused.
    """
    program = to_program(run)

    external: dict[str, Any] = {}
    for address in external_addresses:
        value = pxc.get(address)  # fail-loud (core.py:56-60): a record never invents inputs
        if is_jsonable(value):
            external[address] = value
            continue
        if record_path is None:
            raise RetainError(
                f"retain_run: external '{address}' is a {type(value).__name__} that JSON "
                f"cannot describe and needs a sidecar; pass record_path"
            )
        described = describe(value, f"external['{address}']")
        text = canonical_json(described) + "\n"
        stem = os.path.splitext(os.path.basename(record_path))[0]
        ref = f"{stem}.external.{_safe_name(address)}.json"
        target = os.path.join(os.path.dirname(os.path.abspath(record_path)), ref)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        external[address] = {
            "digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "ref": ref,
        }

    return {
        "program": program,
        "external": external,
        "provider": provider_identity(registry),
        "results": {invocation_id: digest_of(value) for invocation_id, value in run.results.items()},
    }


def write_record(record: Mapping[str, Any], record_path: str) -> str:
    """Write the record as LF JSON; returns the path. Sidecars were written by retain_run."""
    os.makedirs(os.path.dirname(os.path.abspath(record_path)), exist_ok=True)
    with open(record_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return record_path


def replay(record: Mapping[str, Any], registry: Mapping[str, Any]) -> tuple[PxC, PcrRun]:
    """Seed a fresh PxC from the record's JSON externals and re-run the rebuilt program.

    Externals held as {"digest", "ref"} are not reconstructed here: a digest is not
    a value. Such a record replays only if the caller seeds those addresses itself.
    """
    pcr = from_program(record["program"], registry)
    pxc = PxC()
    for address, value in record.get("external", {}).items():
        if isinstance(value, Mapping) and "digest" in value and "ref" in value:
            continue
        pxc.set(Part(address), value)
    return pxc, pcr.run(pxc)
