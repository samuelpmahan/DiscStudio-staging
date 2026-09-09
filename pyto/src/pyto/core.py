from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

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
(``pcr.py:_refuse_receipt_into``). ``PxC`` itself still stores any address: this is
the name the binder checks against, not a rule ``set`` enforces.
"""


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

    def set(self, part: Part[T] | str, value: T) -> PxWrite:
        address = self._address(part)
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
