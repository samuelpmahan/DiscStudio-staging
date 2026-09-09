from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Mapping

from .core import Calculation, Part, PxC, PxWrite


@dataclass(frozen=True, slots=True)
class ResultRef:
    calculation_id: str


@dataclass(frozen=True, slots=True)
class Binding:
    source: Part[Any] | ResultRef


@dataclass(slots=True)
class Invocation:
    id: str
    calculation: Calculation[Any, Any]
    bindings: dict[str, Binding] = field(default_factory=dict)
    args: dict[str, Any] = field(default_factory=dict)
    into: Part[Any] | None = None


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
        into: Part[Any] | str | None = None,
        args: Mapping[str, Any] | None = None,
        **inputs: Part[Any] | ResultRef,
    ) -> ResultRef:
        if any(existing.id == id for existing in self.calculations):
            raise ValueError(f"Tick '{self.name}' has duplicate calculation id '{id}'")
        output = Part(into) if isinstance(into, str) else into
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
    id: str
    calculation: str
    inputs: dict[str, str]
    args: dict[str, Any]
    into: str | None


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
    off. It is empty unless PCR.run was called with observe=True.
    """

    pcr: str
    ticks: tuple[TickTestimony, ...]
    results: dict[str, Any]
    receipts: dict[str, Receipt] = field(default_factory=dict)


def _address(part: Part[Any] | str) -> str:
    return part if isinstance(part, str) else part.address


def _implementation_sha256(function: Any) -> str | None:
    """sha256 of inspect.getsource(function), or None when the source is unavailable."""
    try:
        source = inspect.getsource(function)
    except (OSError, TypeError):
        return None
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


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
        into: Part[Any] | str | None = None,
        args: Mapping[str, Any] | None = None,
        **inputs: Part[Any] | ResultRef,
    ) -> ResultRef:
        if id in self._ids:
            raise ValueError(f"PCR '{self.name}' has duplicate calculation id '{id}'")

        normalized: dict[str, Part[Any] | ResultRef] = {}
        for name, source in inputs.items():
            if isinstance(source, Part) and source.address in self._writers:
                source = ResultRef(self._writers[source.address])
            normalized[name] = source

        output = Part(into) if isinstance(into, str) else into
        if output is not None:
            prior = self._writers.get(output.address)
            if prior is not None:
                raise ValueError(f"PCR '{self.name}' has multiple writers for '{output.address}'")
            self._writers[output.address] = id

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
        not an observation of the callable itself (see Receipt). Observation adds
        fields to PcrRun only: the testimony in `ticks` is byte-identical with
        observe on or off.
        """
        results: dict[str, Any] = {}
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
                        resolved_inputs[name] = results[source.calculation_id]
                        input_refs[name] = f"fn:{source.calculation_id}"

                call_args = dict(resolved_inputs)
                call_args.update(invocation.args)
                value = board.call(invocation.calculation, call_args)
                results[invocation.id] = value
                if invocation.into is not None:
                    board.set(invocation.into, value)

                if isinstance(board, _TrackedPxC):
                    duration_ms = (perf_counter() - started) * 1000.0
                    receipts[invocation.id] = Receipt(
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
                        declared_produces=(
                            () if invocation.into is None else (invocation.into.address,)
                        ),
                        actual_consumes=tuple(board.consumed),
                        actual_produces=tuple(board.produced),
                        writes=tuple(board.writes),
                        result_sha256=_result_sha256(value),
                        effective_arg_keys=tuple(call_args),
                        # call_args.update(invocation.args) above overrides a same-named
                        # bound input silently; the receipt records the collision, it does
                        # not raise ({?} ShadowRule, research/lab-transfer-ledger.md:65-67).
                        shadowed_inputs=tuple(
                            name for name in resolved_inputs if name in invocation.args
                        ),
                    )

                calc_testimony.append(
                    CalculationTestimony(
                        id=invocation.id,
                        calculation=invocation.calculation.address,
                        inputs=input_refs,
                        args=dict(invocation.args),
                        into=invocation.into.address if invocation.into else None,
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
                if invocation.into:
                    pid(invocation.into.address)

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
                if invocation.into:
                    lines.append(f"    {invocation.id} --> {pid(invocation.into.address)}")

        return "\n".join(lines) + "\n"
