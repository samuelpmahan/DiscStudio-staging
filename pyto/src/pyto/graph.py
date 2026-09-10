from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json


@dataclass(frozen=True)
class PartRef:
    address: str


@dataclass(frozen=True)
class ValueRef:
    """A reference to what one calculation produced.

    `produce` names which published Part is meant, for a calculation that declared
    several; it is None for the one-address case, so a graph that publishes one
    Part per calculation emits exactly the document it always did.
    """

    calc_id: str
    produce: str | None = None

    @property
    def ref(self) -> str:
        """The emitted spelling: `<id>`, or `<id>#<address>` for one of several."""
        return self.calc_id if self.produce is None else f"{self.calc_id}#{self.produce}"


@dataclass
class Calculation:
    """One authored call. `into` is one PartRef, a tuple of them, or None.

    A Calculation may publish several Parts from one pass ({?} WhatIsATick, owner
    2026-09-10), so every reader here walks `produce_addresses()` rather than a
    single `into.address` -- the same helper name `pyto.pcr.Invocation` carries,
    so the two authoring surfaces are read the same way.
    """

    id: str
    call: str
    tick: str
    bindings: dict[str, PartRef | ValueRef] = field(default_factory=dict)
    args: dict[str, Any] = field(default_factory=dict)
    into: PartRef | tuple[PartRef, ...] | None = None

    def produce_addresses(self) -> tuple[str, ...]:
        """Every address this calculation publishes, in the declared order."""
        if self.into is None:
            return ()
        if isinstance(self.into, PartRef):
            return (self.into.address,)
        return tuple(ref.address for ref in self.into)

    def emitted_into(self) -> str | list[str] | None:
        """`into` as the emitted document carries it: an address, or an array."""
        if self.into is None:
            return None
        return self.into.address if isinstance(self.into, PartRef) else list(self.produce_addresses())


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
        self._multi: set[str] = set()  # ids that publish several Parts

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
        into: str | list[str] | tuple[str, ...] | None = None,
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
                writer = self._writers[ref.address]
                # When the writer published several Parts, the address written here
                # is which one this binding meant; a one-address writer keeps the
                # bare reference it always had.
                ref = ValueRef(writer, ref.address if writer in self._multi else None)
            normalized[key] = ref

        if into is None or isinstance(into, str):
            output = PartRef(into) if into else None
            outputs = (output,) if output is not None else ()
        else:
            # A list or a tuple is the multi-produce form, even with one entry --
            # the shape decides, not the count (pyto/src/pyto/pcr.py `Invocation`).
            outputs = tuple(PartRef(address) for address in into)
            if not outputs:
                raise ValueError(f"{id}: into=[] declares no address")
            output = outputs
        for ref in outputs:  # every address checked before any is claimed
            if ref.address in self._writers:
                raise ValueError(f"multiple writers for {ref.address}")
        for ref in outputs:
            self._writers[ref.address] = id
        if not isinstance(output, PartRef) and output is not None:
            self._multi.add(id)

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
                            else {"kind": "fn", "ref": ref.ref}
                        )
                        for key, ref in calc.bindings.items()
                    },
                    "args": calc.args,
                }
                if calc.into:
                    item["into"] = calc.emitted_into()
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
            for address in calc.produce_addresses():
                part_id(address)

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
            for address in calc.produce_addresses():
                lines.append(f"    {calc.id} --> {part_id(address)}")

        return "\n".join(lines) + "\n"
