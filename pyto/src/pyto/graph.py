from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json


@dataclass(frozen=True)
class PartRef:
    address: str


@dataclass(frozen=True)
class ValueRef:
    calc_id: str


@dataclass
class Calculation:
    id: str
    call: str
    tick: str
    bindings: dict[str, PartRef | ValueRef] = field(default_factory=dict)
    args: dict[str, Any] = field(default_factory=dict)
    into: PartRef | None = None


class Pcr:
    """Tiny experimental Python authoring surface for ChainSpot PCR graphs.

    This deliberately does not execute ChainSpot calculations. It composes the same
    small graph shape used by the S0/S1 Mermaid proof and can emit PCR JSON plus a
    Mermaid view. Execution remains owned by ChainSpot/PxC.
    """

    def __init__(self, name: str):
        self.name = name
        self._ticks: list[str] = []
        self._calcs: list[Calculation] = []
        self._writers: dict[str, str] = {}

    def part(self, address: str) -> PartRef:
        return PartRef(address)

    def calc(
        self,
        tick: str,
        call: str,
        /,
        *,
        id: str,
        args: dict[str, Any] | None = None,
        into: str | None = None,
        **inputs: PartRef | ValueRef,
    ) -> ValueRef:
        if any(calc.id == id for calc in self._calcs):
            raise ValueError(f"duplicate calculation id: {id}")
        if tick not in self._ticks:
            self._ticks.append(tick)

        normalized: dict[str, PartRef | ValueRef] = {}
        for key, ref in inputs.items():
            if not isinstance(ref, (PartRef, ValueRef)):
                raise TypeError(f"input {id}.{key} must be a PartRef or ValueRef")
            # Match the Mermaid compiler's direct-result behavior: once a Part has a
            # writer in this graph, consuming that Part refers to the writer result.
            if isinstance(ref, PartRef) and ref.address in self._writers:
                ref = ValueRef(self._writers[ref.address])
            normalized[key] = ref

        output = PartRef(into) if into else None
        if output:
            if output.address in self._writers:
                raise ValueError(f"multiple writers for {output.address}")
            self._writers[output.address] = id

        self._calcs.append(
            Calculation(
                id=id,
                call=call,
                tick=tick,
                bindings=normalized,
                args=args or {},
                into=output,
            )
        )
        return ValueRef(id)

    def to_pcr_dict(self) -> dict[str, Any]:
        ticks: list[dict[str, Any]] = []
        for tick in self._ticks:
            calculations: list[dict[str, Any]] = []
            for calc in (candidate for candidate in self._calcs if candidate.tick == tick):
                item: dict[str, Any] = {
                    "id": calc.id,
                    "call": calc.call,
                    "with": {
                        key: (
                            {"kind": "px", "ref": ref.address}
                            if isinstance(ref, PartRef)
                            else {"kind": "fn", "ref": ref.calc_id}
                        )
                        for key, ref in calc.bindings.items()
                    },
                    "args": calc.args,
                }
                if calc.into:
                    item["into"] = calc.into.address
                calculations.append(item)
            ticks.append({"name": tick, "Calculations": calculations})
        return {"PrincipleComponentRender": self.name, "Ticks": ticks}

    def to_pcr_json(self) -> str:
        return json.dumps(self.to_pcr_dict(), indent=2) + "\n"

    def to_mermaid(self) -> str:
        lines = ["flowchart TD"]
        part_ids: dict[str, str] = {}

        def part_id(address: str) -> str:
            if address not in part_ids:
                part_ids[address] = f"p{len(part_ids)}"
            return part_ids[address]

        for calc in self._calcs:
            for ref in calc.bindings.values():
                if isinstance(ref, PartRef):
                    part_id(ref.address)
            if calc.into:
                part_id(calc.into.address)

        for address, node_id in part_ids.items():
            lines.append(f'    {node_id}["{address}"]')

        lines.extend(["", f'    subgraph PCR["PCR: {self.name}"]'])
        for tick in self._ticks:
            safe_tick = "".join(ch if ch.isalnum() else "_" for ch in tick)
            lines.append(f'        subgraph Tick_{safe_tick}["Tick: {tick}"]')
            for calc in (candidate for candidate in self._calcs if candidate.tick == tick):
                lines.append(f'            {calc.id}["{calc.call}"]')
            lines.append("        end")
        lines.extend(["    end", ""])

        for calc in self._calcs:
            for key, ref in calc.bindings.items():
                source = part_id(ref.address) if isinstance(ref, PartRef) else ref.calc_id
                lines.append(f"    {source} -->|{key}| {calc.id}")
            if calc.into:
                lines.append(f"    {calc.id} --> {part_id(calc.into.address)}")

        return "\n".join(lines) + "\n"
