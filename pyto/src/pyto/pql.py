from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, TypeVar

from .core import RECEIPT_PREFIX, Part, PxC

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

    @staticmethod
    def receipts(pxc: PxC, pcr: str | None = None, tick: str | None = None) -> tuple[Match, ...]:
        """The receipt Parts in ``pxc``, address-sorted, narrowed by name segments.

        The address scheme is one line and a reader predicts it from the PCR alone
        (``viewer/RECORD.md``, "Receipts as Parts"; ``pcr.py:receipt_address``)::

            px.receipt.<pcr>.<tick>.<invocation-id>

        so ``pcr`` matches the segment after ``px.receipt.`` and ``tick`` the one
        after that; both omitted is every receipt in the store.  This is a thin
        layer over :meth:`prefix`, which already walks ``pxc.items()`` in address
        order, so the result is sorted and is a pure function of the store.

        The narrowing is by segment and not by string prefix, so ``pcr="fit"``
        does not match a PCR named ``fitting``.  A PCR or Tick name that carries a
        dot puts more segments into the address than the scheme has and shifts
        what ``tick`` matches; that is the open
        ``{?} ReceiptNameSegments`` (``experiments/tasks/22/packet.md``), left
        undecided here rather than papered over -- this reads the address exactly
        as ``receipt_address`` writes it.

        Receipts are read like anything else; only *producing* into
        ``px.receipt.`` is refused (``pcr.py:_refuse_receipt_into``,
        ``core.PxC.set``).
        """
        wanted = {index: segment for index, segment in enumerate((pcr, tick)) if segment is not None}
        if any(segment == "" for segment in wanted.values()):
            raise ValueError("PQL.receipts: pcr and tick must be non-empty when given")
        if not wanted:
            return PQL.prefix(RECEIPT_PREFIX).matches(pxc)

        def narrows(match: Match) -> bool:
            segments = match.address[len(RECEIPT_PREFIX):].split(".")
            return all(
                index < len(segments) and segments[index] == segment
                for index, segment in wanted.items()
            )

        # A leading `pcr` narrows the walk to a prefix; `tick` alone cannot, since the
        # PCR name sits in front of it, so it is a filter over every receipt.
        start = f"{RECEIPT_PREFIX}{pcr}.{tick}." if pcr and tick else (
            f"{RECEIPT_PREFIX}{pcr}." if pcr else RECEIPT_PREFIX
        )
        described = " ".join(segment for _, segment in sorted(wanted.items()))
        return PQL(
            PQL.prefix(start).where(narrows)._select, f"{RECEIPT_PREFIX}* {described}"
        ).matches(pxc)

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
