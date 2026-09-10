from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterator, TypeVar

T = TypeVar("T")
Args = TypeVar("Args")
Result = TypeVar("Result")


@dataclass(frozen=True, slots=True)
class Part(Generic[T]):
    """A semantic PxC address. Identity is the address, not the current value."""

    address: str

    def __post_init__(self) -> None:
        if not self.address:
            raise ValueError("Part address must be non-empty")

    def __str__(self) -> str:
        return self.address


@dataclass(frozen=True, slots=True)
class Calculation(Generic[Args, Result]):
    """A named calculation that PxC can register and PCR can compose."""

    address: str
    calculate: Callable[[Args], Result]

    def __post_init__(self) -> None:
        if not self.address.startswith("fn."):
            raise ValueError("Calculation address must start with 'fn.'")

    def __call__(self, args: Args) -> Result:
        return self.calculate(args)


RECEIPT_PREFIX = "px.receipt."
"""The reserved receipt segment (address.py: six reserved second segments under ``px``).

Addresses under it are written by ``PCR.run(..., observe=True)`` only
(``pcr.py:receipt_address``); a Calculation may not bind one as its ``into``
(``pcr.py:_refuse_receipt_into``), and since task 41 ``PxC.set`` refuses one too
unless the write is the run's own (``_receipt_write_is_the_run_s``).
"""

RUN_MODULE = "pyto.pcr"
"""The one module whose ``PxC.set`` calls may write under ``RECEIPT_PREFIX``.

``pcr.py`` is another team's file and is not edited for this guard, so the guard
recognises the run by the module the calling frame belongs to rather than by an
argument ``pcr.py`` does not pass yet.
"""

_receipt_writes_open = 0


@contextmanager
def receipt_writes_allowed() -> Iterator[None]:
    """Open ``px.receipt.`` to ``PxC.set`` for the duration of the block.

    The explicit form of the guard's exception, for a caller that files receipts
    without living in :data:`RUN_MODULE` -- a future ``pcr.py`` that would rather
    say so than be recognised by its frame, a replayer rebuilding a store from a
    record, a test. Re-entrant, single-threaded, and restored on the way out even
    when the block raises.
    """
    global _receipt_writes_open
    _receipt_writes_open += 1
    try:
        yield
    finally:
        _receipt_writes_open -= 1


def _receipt_write_is_the_run_s(depth: int) -> bool:
    """True when the ``PxC.set`` ``depth`` frames up is the run filing its own receipt.

    The rule, chosen for being deterministic and needing no edit to ``pcr.py``:
    a write under ``px.receipt.`` is the run's when it is inside an open
    :func:`receipt_writes_allowed` block, or when the frame that called
    ``PxC.set`` belongs to :data:`RUN_MODULE`.  Nothing about timing, ordering or
    the value is consulted, so the answer is a pure function of who is calling.

    A caller with no Python frame at ``depth`` (an interpreter without frame
    support) is not the run: the guard refuses rather than guesses.
    """
    if _receipt_writes_open:
        return True
    try:
        frame = sys._getframe(depth)
    except ValueError:  # pragma: no cover - no caller frame to inspect
        return False
    return frame.f_globals.get("__name__") == RUN_MODULE


def _refuse_forged_receipt(address: str) -> None:
    # 0 _receipt_write_is_the_run_s, 1 here, 2 PxC.set, 3 whoever called set.
    if _receipt_write_is_the_run_s(3):
        return
    raise ValueError(
        f"PxC: '{address}' is under the reserved '{RECEIPT_PREFIX}' segment, which "
        f"only a run may write ({RUN_MODULE}, or inside receipt_writes_allowed(), "
        "or set(..., _from_run=True))"
    )


@dataclass(frozen=True, slots=True)
class PxWrite:
    address: str
    kind: str


class PxC:
    """Fail-loud semantic Part store plus Calculation registry."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}
        self._calculations: dict[str, Calculation[Any, Any]] = {}

    def has(self, part: Part[Any] | str) -> bool:
        return self._address(part) in self._values

    def get(self, part: Part[T] | str) -> T:
        address = self._address(part)
        if address not in self._values:
            raise KeyError(f"PxC: Part '{address}' has not been produced")
        return self._values[address]

    def set(self, part: Part[T] | str, value: T, *, _from_run: bool = False) -> PxWrite:
        """Store ``value`` at ``part``'s address.

        ``_from_run`` is the run's marker: ``PcrRun``'s observe branch passes it
        when it files a receipt.  Without it a write under ``RECEIPT_PREFIX`` is
        refused unless :func:`_receipt_write_is_the_run_s` recognises the caller,
        so the reserved segment is reserved against callers and not only against
        programs (``experiments/tasks/22/packet.md`` ``{?} ReceiptStoreSetUnguarded``).
        """
        address = self._address(part)
        if address.startswith(RECEIPT_PREFIX) and not _from_run:
            _refuse_forged_receipt(address)
        kind = "replacement" if address in self._values else "new-address"
        self._values[address] = value
        return PxWrite(address, kind)

    def register(self, calculation: Calculation[Any, Any]) -> None:
        current = self._calculations.get(calculation.address)
        if current is not None and current.calculate is not calculation.calculate:
            raise ValueError(f"PxC: Calculation '{calculation.address}' is already registered")
        self._calculations[calculation.address] = calculation

    def call(self, calculation: Calculation[Args, Result] | str, args: Args) -> Result:
        address = calculation if isinstance(calculation, str) else calculation.address
        registered = self._calculations.get(address)
        if registered is None:
            if isinstance(calculation, Calculation):
                self.register(calculation)
                registered = calculation
            else:
                raise KeyError(f"PxC: Calculation '{address}' is not registered")
        return registered.calculate(args)

    def addresses(self) -> tuple[str, ...]:
        return tuple(sorted(self._values))

    def items(self) -> tuple[tuple[str, Any], ...]:
        return tuple((address, self._values[address]) for address in sorted(self._values))

    @staticmethod
    def _address(part: Part[Any] | str) -> str:
        return part if isinstance(part, str) else part.address
