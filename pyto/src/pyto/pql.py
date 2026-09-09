from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, TypeVar

from .core import Part, PxC

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Match:
    address: str
    value: Any


class PQL(Generic[T]):
    """Tiny composable query over PxC.

    Exact Parts and address prefixes are first-class; refinement stays ordinary Python.
    """

    def __init__(self, select: Callable[[PxC], Iterable[Match]], description: str) -> None:
        self._select = select
        self.description = description

    @classmethod
    def part(cls, part: Part[T] | str) -> "PQL[T]":
        address = part if isinstance(part, str) else part.address

        def select(pxc: PxC) -> Iterable[Match]:
            if pxc.has(address):
                yield Match(address, pxc.get(address))

        return cls(select, address)

    @classmethod
    def prefix(cls, prefix: str) -> "PQL[Any]":
        if not prefix:
            raise ValueError("PQL prefix must be non-empty")

        def select(pxc: PxC) -> Iterable[Match]:
            for address, value in pxc.items():
                if address.startswith(prefix):
                    yield Match(address, value)

        return cls(select, f"{prefix}*")

    def where(self, predicate: Callable[[Match], bool]) -> "PQL[T]":
        parent = self

        def select(pxc: PxC) -> Iterable[Match]:
            return (match for match in parent.matches(pxc) if predicate(match))

        return PQL(select, f"{self.description} where …")

    def matches(self, pxc: PxC) -> tuple[Match, ...]:
        return tuple(self._select(pxc))

    def values(self, pxc: PxC) -> tuple[T, ...]:
        return tuple(match.value for match in self.matches(pxc))

    def one(self, pxc: PxC) -> T:
        matches = self.matches(pxc)
        if len(matches) != 1:
            raise ValueError(f"PQL '{self.description}' expected exactly 1 match; got {len(matches)}")
        return matches[0].value

    def optional(self, pxc: PxC) -> T | None:
        matches = self.matches(pxc)
        if len(matches) > 1:
            raise ValueError(f"PQL '{self.description}' expected at most 1 match; got {len(matches)}")
        return matches[0].value if matches else None
