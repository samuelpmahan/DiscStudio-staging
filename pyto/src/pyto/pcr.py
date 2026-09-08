from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .core import Calculation, Part, PxC


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
class PcrRun:
    pcr: str
    ticks: tuple[TickTestimony, ...]
    results: dict[str, Any]


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

    def run(self, pxc: PxC) -> PcrRun:
        results: dict[str, Any] = {}
        testimonies: list[TickTestimony] = []

        for tick in self.ticks:
            calc_testimony: list[CalculationTestimony] = []
            for invocation in tick.calculations:
                pxc.register(invocation.calculation)
                resolved_inputs: dict[str, Any] = {}
                input_refs: dict[str, str] = {}
                for name, binding in invocation.bindings.items():
                    source = binding.source
                    if isinstance(source, Part):
                        resolved_inputs[name] = pxc.get(source)
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
                value = pxc.call(invocation.calculation, call_args)
                results[invocation.id] = value
                if invocation.into is not None:
                    pxc.set(invocation.into, value)

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

        return PcrRun(self.name, tuple(testimonies), results)

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
