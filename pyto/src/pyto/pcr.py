from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Mapping

from .core import RECEIPT_PREFIX, Calculation, Part, PxC, PxWrite


@dataclass(frozen=True, slots=True)
class ResultRef:
    """A reference to what one invocation returned.

    `produce` names *which* published Part is meant. It is None for a bare
    reference -- the whole returned value -- which is all a one-address
    invocation has. An invocation that declares several `into` addresses
    publishes one Part per address from one returned value, so a bare reference
    to it is ambiguous and `PCR` refuses it ({?} WhatIsATick, owner 2026-09-10:
    "Obviously a Calculation can produce multiple parts"); `ref[address]` and
    `ref.part(address)` are the two spellings that name one.
    """

    calculation_id: str
    produce: str | None = None

    def part(self, address: "Part[Any] | str") -> "ResultRef":
        """This invocation's produce at `address` (a Part or a bare address)."""
        return ResultRef(self.calculation_id, _address(address))

    def __getitem__(self, address: "Part[Any] | str") -> "ResultRef":
        return self.part(address)


def _ref_spelling(ref: ResultRef) -> str:
    """The testimony spelling of a result binding: `fn:<id>`, or `fn:<id>#<address>`.

    One address per invocation needs no qualifier, so a one-address program's
    testimony is the byte it always was; a produce-qualified reference carries the
    address after `#` (viewer/RECORD.md, Field rules).
    """
    return f"fn:{ref.calculation_id}" if ref.produce is None else f"fn:{ref.calculation_id}#{ref.produce}"


@dataclass(frozen=True, slots=True)
class Binding:
    source: Part[Any] | ResultRef


@dataclass(slots=True)
class Invocation:
    """One authored call. `into` is one Part, a tuple of Parts, or None.

    The *shape* decides, not the count: `into=Part("a")` publishes the returned
    value at one address and `into=[Part("a")]` is a one-entry multi-produce
    invocation whose Calculation returns a mapping or a sequence. A tuple is
    always the multi-produce form (`is_multi`), so a program cannot slide from
    one meaning to the other by the length of a computed list.
    """

    id: str
    calculation: Calculation[Any, Any]
    bindings: dict[str, Binding] = field(default_factory=dict)
    args: dict[str, Any] = field(default_factory=dict)
    into: Part[Any] | tuple[Part[Any], ...] | None = None

    def is_multi(self) -> bool:
        return isinstance(self.into, tuple)

    def produces(self) -> tuple[Part[Any], ...]:
        """Every Part this invocation publishes, in the declared order."""
        if self.into is None:
            return ()
        return self.into if isinstance(self.into, tuple) else (self.into,)

    def produce_addresses(self) -> tuple[str, ...]:
        return tuple(part.address for part in self.produces())

    def testimony_into(self) -> str | tuple[str, ...] | None:
        """`into` as the testimony and the run record carry it: an address, or a list."""
        if self.into is None:
            return None
        return self.produce_addresses() if isinstance(self.into, tuple) else self.into.address


def receipt_address(pcr: str, tick: str, invocation_id: str) -> str:
    """The one address scheme: ``px.receipt.<pcr>.<tick>.<invocation-id>``.

    Predictable from the PCR alone -- the invocation id is what `PCR.calc` already
    keeps unique (`PCR._ids`), so no invocation index is needed and no two
    invocations of one run can collide, not even two invocations of the same
    Calculation in the same Tick (`fit.all` and `fit.none` in the Day 1 program).
    Written by `PCR.run(..., observe=True)` only; see viewer/RECORD.md.
    """
    return f"{RECEIPT_PREFIX}{pcr}.{tick}.{invocation_id}"


def _refuse_receipt_into(owner: str, output: Part[Any] | None) -> None:
    """Refuse, at bind time, a Calculation whose `into` is under `px.receipt.`.

    The receipt segment is written by observation and by nothing else, so a program
    that produced into it would be forging its own testimony.
    """
    if output is not None and output.address.startswith(RECEIPT_PREFIX):
        raise ValueError(
            f"{owner} may not bind '{output.address}': the reserved '{RECEIPT_PREFIX}' "
            "segment is written by PCR.run(..., observe=True) and by nothing else; "
            "no Calculation may produce into it"
        )


def _normalize_into(
    owner: str, into: Part[Any] | str | list[Any] | tuple[Any, ...] | None
) -> Part[Any] | tuple[Part[Any], ...] | None:
    """One address, several addresses, or none -- as a Part, a tuple of Parts, or None.

    A list or a tuple is the multi-produce form even when it holds one entry (see
    `Invocation`). Every address is refused under the reserved receipt segment, and
    an address declared twice in one invocation is refused here rather than silently
    publishing the second value over the first.
    """
    if into is None:
        return None
    if isinstance(into, (str, Part)):
        output = Part(into) if isinstance(into, str) else into
        _refuse_receipt_into(owner, output)
        return output
    if not isinstance(into, (list, tuple)):
        raise ValueError(
            f"{owner} has into={into!r}: expected an address, a Part, or a list of them"
        )
    if not into:
        raise ValueError(
            f"{owner} has into=[]: a Calculation produces one Part, several, or none "
            "(into=None), never an empty list of them"
        )
    outputs: list[Part[Any]] = []
    for entry in into:
        if not isinstance(entry, (str, Part)):
            raise ValueError(
                f"{owner} has {entry!r} in its into list: every entry must be an address or a Part"
            )
        output = Part(entry) if isinstance(entry, str) else entry
        _refuse_receipt_into(owner, output)
        if any(existing.address == output.address for existing in outputs):
            raise ValueError(
                f"{owner} declares '{output.address}' twice in into: one invocation "
                "publishes each address once"
            )
        outputs.append(output)
    return tuple(outputs)


def _refuse_bare_multi_ref(owner: str, ref: ResultRef, addresses: tuple[str, ...]) -> None:
    """Refuse a bare reference to an invocation that publishes several Parts.

    The whole returned value of a multi-produce Calculation is the carrier of its
    produces, not a result in its own right, so a binding has to say which one it
    means. Named at bind time by `PCR.calc` and at resolve time by `PCR.run`, so a
    program built through `Tick.calc` alone is refused too.
    """
    raise ValueError(
        f"{owner} binds the whole result of '{ref.calculation_id}', which produces "
        f"{len(addresses)} Parts ({', '.join(addresses)}); name the one it means -- "
        f"ref['{addresses[0]}'] or ref.part('{addresses[0]}')"
    )


@dataclass(slots=True)
class Tick:
    name: str
    calculations: list[Invocation] = field(default_factory=list)

    def calc(
        self,
        calculation: Calculation[Any, Any],
        /,
        *,
        id: str,
        into: Part[Any] | str | list[Any] | tuple[Any, ...] | None = None,
        args: Mapping[str, Any] | None = None,
        **inputs: Part[Any] | ResultRef,
    ) -> ResultRef:
        if any(existing.id == id for existing in self.calculations):
            raise ValueError(f"Tick '{self.name}' has duplicate calculation id '{id}'")
        output = _normalize_into(f"Tick '{self.name}' calculation '{id}'", into)
        bindings = {name: Binding(source) for name, source in inputs.items()}
        self.calculations.append(
            Invocation(
                id=id,
                calculation=calculation,
                bindings=bindings,
                args=dict(args or {}),
                into=output,
            )
        )
        return ResultRef(id)


@dataclass(frozen=True, slots=True)
class CalculationTestimony:
    """`into` is one address, a tuple of addresses (a multi-produce invocation), or None.

    A one-address invocation still testifies a bare string, so the bytes consumers
    embed are unchanged by this kernel's ability to publish several Parts.
    """

    id: str
    calculation: str
    inputs: dict[str, str]
    args: dict[str, Any]
    into: str | tuple[str, ...] | None


@dataclass(frozen=True, slots=True)
class TickTestimony:
    name: str
    calculations: tuple[CalculationTestimony, ...]


@dataclass(frozen=True, slots=True)
class FrozenCalculation:
    """One executable Calculation frozen at the moment an invocation ran.

    Transferred from reference/lab/chesslab-lab/contract.ts:60-68, honesty fields
    included: `implementation_sha256` is the digest of this runtime's function
    body only. It is not a transitive source or dependency hash, and it is None
    when the runtime cannot show the source (a C builtin, an interactively
    defined function).
    """

    address: str
    implementation_sha256: str | None
    identity_scope: str = "runtime-function-body"
    limitation: str = "called helpers, constants, templates, and assets are not covered"


@dataclass(frozen=True, slots=True)
class Receipt:
    """What PCR.run observed while executing one invocation.

    Transferred from reference/lab/chesslab-lab/contract.ts:127-141 (Receipt) and
    reference/lab/wumpus-core/execute.js:10-47 (executeTick). `declared_*` comes
    from the authored program: the invocation's bound Part addresses and its
    `into`. `actual_*` and `writes` come from a tracked view of the PxC
    (_TrackedPxC, after ../../src/core/exec.js:22-33 trackAccess).

    Honest scope: PCR.run performs every read and write on the invocation's
    behalf -- it resolves the bindings and then calls the Calculation with a
    plain args mapping -- so `actual_consumes`, `actual_produces` and `writes`
    are what PCR.run observed, NOT what the callable touched. A Calculation body
    that closed over a PxC and read or wrote it directly is invisible here.

    Two digests, because a Calculation may publish several Parts from one pass
    ({?} WhatIsATick, decided by the owner 2026-09-10). `result_sha256` is the
    digest of the whole returned value and is what it always was -- for a
    one-address invocation the returned value *is* the published Part, so the
    field is unchanged there. `produce_sha256` is one digest per published
    address, `{address: sha256 or None}` in declared order: it is the honest
    per-Part answer when one invocation publishes several, and for a one-address
    invocation it is `{into: result_sha256}`. Both use `_result_sha256`, so a
    non-JSON value has no digest rather than an unstable one.

    This receipt records digests and durations only. It makes no external-input
    boundary decision and is not the replay seam
    (docs/PYTHON-LAB-STEWARDSHIP.md:62; CHANGES.md).
    """

    invocation_id: str
    calculation: FrozenCalculation
    started_ms: float
    duration_ms: float
    declared_consumes: tuple[str, ...]
    declared_produces: tuple[str, ...]
    actual_consumes: tuple[str, ...]
    actual_produces: tuple[str, ...]
    writes: tuple[PxWrite, ...]
    result_sha256: str | None
    produce_sha256: dict[str, str | None]
    effective_arg_keys: tuple[str, ...]
    shadowed_inputs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PcrRun:
    """Testimony of one execution.

    `receipts` is additive and trailing on purpose: `pcr`, `ticks` and `results`
    keep their shape, so json.dumps([asdict(t) for t in run.ticks]) -- the bytes
    consumers embed in compositionEvidence
    (consumers/discstudio-card/card_composition.py:177,
    consumers/discstudio-card/app.py:53) -- is byte-identical with observe on or
    off. It is empty unless PCR.run was called with observe=True, in which case the
    same Receipts are also Parts in the store under `px.receipt.` (see PCR.run).
    """

    pcr: str
    ticks: tuple[TickTestimony, ...]
    results: dict[str, Any]
    receipts: dict[str, Receipt] = field(default_factory=dict)


def _address(part: Part[Any] | str) -> str:
    return part if isinstance(part, str) else part.address


def _implementation_sha256(function: Any) -> str | None:
    """sha256 of inspect.getsource(function) with line endings normalized to LF, or None
    when the source is unavailable.

    Normalized so the digest is the same on every checkout: a Windows clone with CRLF
    endings must not make every retained record look like its implementation changed.
    """
    try:
        source = inspect.getsource(function)
    except (OSError, TypeError):
        return None
    return hashlib.sha256(source.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _result_sha256(value: Any) -> str | None:
    """sha256 of canonical JSON, or None when the value is not JSON.

    Deliberately without `default=`: with a fallback serializer every value gets a
    digest, non-JSON values are digested through their repr, and a repr carrying an
    object address makes the digest process-dependent (ULTRACODE-WEEK.md critic gap
    10). A set, a PxC and a dict with tuple keys (the disc-stats result shape,
    consumers/discstudio-card/experiments/disc-stats/stats.py:34) therefore have no
    digest rather than an unstable one.
    """
    try:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _split_produces(owner: str, addresses: tuple[str, ...], value: Any) -> tuple[Any, ...]:
    """One value per declared address, in the declared order.

    A Calculation that declares several `into` addresses returns them together, and
    this is the only place that decides how: a **mapping keyed by the addresses**, or
    a **sequence in the declared order**. Both are accepted because both are honest
    spellings of "one value per address"; a mapping says which is which at the call
    site, a sequence is what a Python function returns when it returns two things.

    Strict in both directions: a missing key, an unexpected key, or a sequence of the
    wrong length is refused rather than published, because the alternative is a Part
    quietly holding the wrong value. Nothing is written until every address has its
    value ({?} MultiReturnStrict).
    """
    if isinstance(value, MappingABC):
        missing = [address for address in addresses if address not in value]
        if missing:
            raise ValueError(
                f"{owner} declares produces {', '.join(addresses)} and returned a mapping "
                f"with no entry for {', '.join(missing)}"
            )
        extra = sorted(str(key) for key in value if key not in addresses)
        if extra:
            raise ValueError(
                f"{owner} declares produces {', '.join(addresses)} and returned a mapping "
                f"carrying {', '.join(extra)} as well; a produce mapping carries the "
                "declared addresses and nothing else"
            )
        return tuple(value[address] for address in addresses)
    if isinstance(value, (list, tuple)):
        if len(value) != len(addresses):
            raise ValueError(
                f"{owner} declares {len(addresses)} produces ({', '.join(addresses)}) and "
                f"returned a sequence of {len(value)}"
            )
        return tuple(value)
    raise ValueError(
        f"{owner} declares {len(addresses)} produces ({', '.join(addresses)}), so its "
        "Calculation must return a mapping keyed by those addresses or a sequence in "
        f"that order; it returned {type(value).__name__}"
    )


class _TrackedPxC:
    """A recording view of a PxC for the span of one invocation.

    Transferred from ../../src/core/exec.js:22-33 (trackAccess): reads are
    appended to `consumed`, writes to `produced` and to `writes` with the
    collision-visible kind of reference/lab/chesslab-lab/contract.ts:71-74 --
    `new-address` when the address did not exist, `refinement` when it existed and
    was among this invocation's declared consumes, `replacement` otherwise. It
    changes no PxC behaviour: every call delegates, and a missing address still
    raises from PxC.get (core.py:56-59).
    """

    __slots__ = ("_pxc", "_declared", "consumed", "produced", "writes")

    def __init__(self, pxc: PxC, declared_consumes: tuple[str, ...]) -> None:
        self._pxc = pxc
        self._declared = frozenset(declared_consumes)
        self.consumed: list[str] = []
        self.produced: list[str] = []
        self.writes: list[PxWrite] = []

    def has(self, part: Part[Any] | str) -> bool:
        return self._pxc.has(part)

    def get(self, part: Part[Any] | str) -> Any:
        address = _address(part)
        if address not in self.consumed:
            self.consumed.append(address)
        return self._pxc.get(part)

    def set(self, part: Part[Any] | str, value: Any) -> PxWrite:
        address = _address(part)
        if not self._pxc.has(part):
            kind = "new-address"
        elif address in self._declared:
            kind = "refinement"
        else:
            kind = "replacement"
        self._pxc.set(part, value)
        if address not in self.produced:
            self.produced.append(address)
        write = PxWrite(address, kind)
        self.writes.append(write)
        return write

    def register(self, calculation: Calculation[Any, Any]) -> None:
        self._pxc.register(calculation)

    def call(self, calculation: Calculation[Any, Any] | str, args: Any) -> Any:
        return self._pxc.call(calculation, args)


class PCR:
    """Executable Python composition of PxC Parts and Calculations."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.ticks: list[Tick] = []
        self._tick_by_name: dict[str, Tick] = {}
        self._writers: dict[str, str] = {}
        # invocation id -> its produce addresses, for the invocations that declare
        # several: what makes a bare ResultRef to one of them refusable at bind
        # time and a Part binding on one of their addresses resolvable to the
        # right produce.
        self._multi_produce: dict[str, tuple[str, ...]] = {}
        self._ids: set[str] = set()

    def tick(self, name: str) -> Tick:
        if name not in self._tick_by_name:
            tick = Tick(name)
            self._tick_by_name[name] = tick
            self.ticks.append(tick)
        return self._tick_by_name[name]

    def calc(
        self,
        tick: str,
        calculation: Calculation[Any, Any],
        /,
        *,
        id: str,
        into: Part[Any] | str | list[Any] | tuple[Any, ...] | None = None,
        args: Mapping[str, Any] | None = None,
        **inputs: Part[Any] | ResultRef,
    ) -> ResultRef:
        if id in self._ids:
            raise ValueError(f"PCR '{self.name}' has duplicate calculation id '{id}'")
        owner = f"PCR '{self.name}' calculation '{id}'"

        normalized: dict[str, Part[Any] | ResultRef] = {}
        for name, source in inputs.items():
            if isinstance(source, ResultRef):
                produces = self._multi_produce.get(source.calculation_id)
                if produces is not None and source.produce is None:
                    _refuse_bare_multi_ref(owner, source, produces)
                if produces is not None and source.produce not in produces:
                    raise ValueError(
                        f"{owner} binds produce '{source.produce}' of "
                        f"'{source.calculation_id}', which publishes {', '.join(produces)}"
                    )
            elif isinstance(source, Part) and source.address in self._writers:
                writer = self._writers[source.address]
                # A Part already written by this PCR is a read of that invocation's
                # result, not of the store. When the writer publishes several Parts
                # the reference has to name which one -- and the address the program
                # wrote here is exactly that answer.
                source = ResultRef(
                    writer, source.address if writer in self._multi_produce else None
                )
            normalized[name] = source

        output = _normalize_into(owner, into)
        outputs = (output,) if isinstance(output, Part) else (output or ())
        for part in outputs:  # every address checked before any is claimed
            if self._writers.get(part.address) is not None:
                raise ValueError(f"PCR '{self.name}' has multiple writers for '{part.address}'")
        for part in outputs:
            self._writers[part.address] = id
        if isinstance(output, tuple):
            self._multi_produce[id] = tuple(part.address for part in output)

        result = self.tick(tick).calc(
            calculation,
            id=id,
            into=output,
            args=args,
            **normalized,
        )
        self._ids.add(id)
        return result

    def run(self, pxc: PxC, *, observe: bool = False) -> PcrRun:
        """Execute every invocation in declaration order and return the testimony.

        With observe=True the run additionally returns one Receipt per invocation
        id in PcrRun.receipts. A Receipt is an observation of what this method did
        on the invocation's behalf -- the reads it resolved, the write it made, the
        arguments it passed, how long the call took, the digest of the result --
        not an observation of the callable itself (see Receipt).

        With observe=True the same Receipt object is also written into the store at
        `receipt_address(pcr, tick, invocation_id)` -- `px.receipt.<pcr>.<tick>.<id>`
        -- so PQL reads receipts like any other Part. With observe=False nothing is
        written: the store is byte-for-byte what the program itself produced.
        Observation adds fields to PcrRun and Parts under the reserved receipt
        segment only: the testimony in `ticks`, the produced results and the run
        record (materialize.run_record) are the same with observe on or off.
        """
        results: dict[str, Any] = {}
        # invocation id -> {published address: the value published there}. A
        # one-address invocation publishes its whole result; a multi-produce one
        # publishes one entry per declared address, which is what `ref[address]`
        # reads.
        published: dict[str, dict[str, Any]] = {}
        multi_ids: set[str] = set()
        testimonies: list[TickTestimony] = []
        receipts: dict[str, Receipt] = {}

        for tick in self.ticks:
            calc_testimony: list[CalculationTestimony] = []
            for invocation in tick.calculations:
                board: PxC | _TrackedPxC = pxc
                declared_consumes: tuple[str, ...] = ()
                started = 0.0
                if observe:
                    declared_consumes = tuple(
                        binding.source.address
                        for binding in invocation.bindings.values()
                        if isinstance(binding.source, Part)
                    )
                    board = _TrackedPxC(pxc, declared_consumes)
                    started = perf_counter()

                board.register(invocation.calculation)
                resolved_inputs: dict[str, Any] = {}
                input_refs: dict[str, str] = {}
                for name, binding in invocation.bindings.items():
                    source = binding.source
                    if isinstance(source, Part):
                        resolved_inputs[name] = board.get(source)
                        input_refs[name] = f"px:{source.address}"
                    else:
                        if source.calculation_id not in results:
                            raise ValueError(
                                f"PCR '{self.name}' calculation '{invocation.id}' depends on "
                                f"unavailable result '{source.calculation_id}'"
                            )
                        owner = f"PCR '{self.name}' calculation '{invocation.id}'"
                        available = published.get(source.calculation_id, {})
                        if source.produce is None:
                            if source.calculation_id in multi_ids:
                                _refuse_bare_multi_ref(owner, source, tuple(available))
                            resolved_inputs[name] = results[source.calculation_id]
                        else:
                            if source.produce not in available:
                                raise ValueError(
                                    f"{owner} binds produce '{source.produce}' of "
                                    f"'{source.calculation_id}', which publishes "
                                    f"{', '.join(available) or 'no Part'}"
                                )
                            resolved_inputs[name] = available[source.produce]
                        input_refs[name] = _ref_spelling(source)

                call_args = dict(resolved_inputs)
                call_args.update(invocation.args)
                value = board.call(invocation.calculation, call_args)
                results[invocation.id] = value
                produce_parts = invocation.produces()
                produce_addresses = invocation.produce_addresses()
                if invocation.is_multi():
                    # Split before writing anything: a return value that does not
                    # answer for every declared address publishes no Part at all.
                    produced_values = _split_produces(
                        f"PCR '{self.name}' calculation '{invocation.id}'",
                        produce_addresses,
                        value,
                    )
                    multi_ids.add(invocation.id)
                else:
                    produced_values = (value,) if produce_parts else ()
                slots = {}
                for part, part_value in zip(produce_parts, produced_values):
                    board.set(part, part_value)
                    slots[part.address] = part_value
                published[invocation.id] = slots

                if isinstance(board, _TrackedPxC):
                    duration_ms = (perf_counter() - started) * 1000.0
                    receipt = Receipt(
                        invocation_id=invocation.id,
                        calculation=FrozenCalculation(
                            address=invocation.calculation.address,
                            implementation_sha256=_implementation_sha256(
                                invocation.calculation.calculate
                            ),
                        ),
                        started_ms=started * 1000.0,
                        duration_ms=duration_ms,
                        declared_consumes=declared_consumes,
                        declared_produces=produce_addresses,
                        actual_consumes=tuple(board.consumed),
                        actual_produces=tuple(board.produced),
                        writes=tuple(board.writes),
                        result_sha256=_result_sha256(value),
                        produce_sha256={
                            address: _result_sha256(part_value)
                            for address, part_value in slots.items()
                        },
                        effective_arg_keys=tuple(call_args),
                        # call_args.update(invocation.args) above overrides a same-named
                        # bound input silently; the receipt records the collision, it does
                        # not raise ({?} ShadowRule, research/lab-transfer-ledger.md:65-67).
                        shadowed_inputs=tuple(
                            name for name in resolved_inputs if name in invocation.args
                        ),
                    )
                    receipts[invocation.id] = receipt
                    # Everything is a Part: the receipt is written into the store under
                    # its reserved segment, so PQL reads it like any other Part. It goes
                    # to `pxc` and not to `board`, and only after the Receipt above is
                    # frozen: the tracked view is this invocation's, and filing a receipt
                    # is not something the invocation did. Written the other way round,
                    # every invocation would testify that it produced its own receipt.
                    pxc.set(receipt_address(self.name, tick.name, invocation.id), receipt)

                calc_testimony.append(
                    CalculationTestimony(
                        id=invocation.id,
                        calculation=invocation.calculation.address,
                        inputs=input_refs,
                        args=dict(invocation.args),
                        into=invocation.testimony_into(),
                    )
                )
            testimonies.append(TickTestimony(tick.name, tuple(calc_testimony)))

        return PcrRun(self.name, tuple(testimonies), results, receipts)

    def mermaid(self) -> str:
        lines = ["flowchart TD"]
        parts: dict[str, str] = {}

        def pid(address: str) -> str:
            if address not in parts:
                parts[address] = f"p{len(parts)}"
            return parts[address]

        for tick in self.ticks:
            for invocation in tick.calculations:
                for binding in invocation.bindings.values():
                    if isinstance(binding.source, Part):
                        pid(binding.source.address)
                for part in invocation.produces():
                    pid(part.address)

        for address, node_id in parts.items():
            lines.append(f'    {node_id}["{address}"]')

        lines.append("")
        lines.append(f'    subgraph PCR["PCR: {self.name}"]')
        for tick in self.ticks:
            safe = "".join(ch if ch.isalnum() else "_" for ch in tick.name)
            lines.append(f'        subgraph Tick_{safe}["Tick: {tick.name}"]')
            for invocation in tick.calculations:
                lines.append(f'            {invocation.id}["{invocation.calculation.address}"]')
            lines.append("        end")
        lines.append("    end")
        lines.append("")

        for tick in self.ticks:
            for invocation in tick.calculations:
                for name, binding in invocation.bindings.items():
                    source = binding.source
                    source_id = pid(source.address) if isinstance(source, Part) else source.calculation_id
                    lines.append(f"    {source_id} -->|{name}| {invocation.id}")
                for part in invocation.produces():
                    lines.append(f"    {invocation.id} --> {pid(part.address)}")

        return "\n".join(lines) + "\n"
