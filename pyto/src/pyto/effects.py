"""The syscall table: the one place an effect happens, and the ledger of it.

Lane 1's statement, in the owner's words (``pyto/BOARD.md``): "Two kinds of
Calculation and no third: ``fn`` is pure; ``oc`` (OperationalCalculation) is the
syscall table, the only place an effect happens (shell, file, git, network), and
it records what it read and what it produced as Parts so replay plays the Part
back instead of re-running the effect."  An OS with no effects is a calculator;
the receipt is the subject, so an effect that is not on a receipt did not happen
as far as this kernel is concerned.

Two handles, one ledger shape:

* :class:`Effects` performs the effect and appends what it did.
* :class:`ReplayEffects` is built from a recorded ledger and **plays it back**:
  ``read_text``, ``now_ms``, ``random`` and ``env`` return the recorded values in
  order and touch nothing outside; ``write_text`` is the one effect that is
  re-performed, because a write is what the run is for, and its digest is
  compared against the recorded one.  Any call that is not the next recorded
  entry is refused, naming the kind and the index.

Five verbs, chosen because they are the effects the week's programs actually make
(``write_text``, ``read_text``, ``now_ms``, ``random``, ``env``) and because each
has an obvious recorded value to feed back.  Everything about them is honest
about scope: an ``oc`` that opens a socket behind this handle's back is invisible
here, exactly as a Calculation that closes over a ``PxC`` is invisible to a
``Receipt`` (``pcr.py``, ``Receipt``).

**Paths are relative.**  Every path is recorded relative to the run's
``effects_root`` and never absolute: a ledger written in one checkout replays in
another, and in the temporary directory a test hands it.  A path that escapes the
root is refused rather than recorded as ``../..``.

**One digest rule.**  ``result_sha256`` is the sha256 of the canonical JSON of
the recorded value -- the same rule as ``pcr._result_sha256`` -- for every kind,
including ``write_text``, whose recorded value is the text that was written
(kept as a digest only: a ledger is not a copy of the file).  One rule means a
reader never has to ask which kind it is looking at before it can compare two
digests.

**The seed is an effect.**  ``random(n)`` draws from a seeded generator, and the
seed comes from outside the program, so the seed is itself a recorded effect
(``random_seed``) and is fed back on replay like any other.  A ledger therefore
reproduces the draws exactly, and a replay that re-seeded itself would be caught
by the first ``random`` entry it failed to match.
"""

from __future__ import annotations

import hashlib
import json
import os
import random as _random
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Iterable

__all__ = [
    "EFFECT_KINDS",
    "Effect",
    "Effects",
    "EffectRefused",
    "ReplayEffects",
    "effect_digest",
]

EFFECT_KINDS: tuple[str, ...] = (
    "write_text",
    "read_text",
    "now_ms",
    "random_seed",
    "random",
    "env",
)
"""Every kind a ledger entry may carry.  A sixth would be a sixth syscall."""


class EffectRefused(ValueError):
    """A replay that did not match the record: wrong kind, wrong args, wrong digest.

    A ``ValueError``, because the caller asked for something the recorded ledger
    does not say happened, and the run stops there rather than inventing a value.
    """


def effect_digest(value: Any) -> str:
    """sha256 of the canonical JSON of ``value`` (``pcr._result_sha256``'s rule).

    Unlike ``_result_sha256`` this never returns ``None``: every recorded effect
    value is JSON by construction (a string, a number, a list of numbers, or
    null), so a ledger entry always carries a digest to compare.
    """
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class Effect:
    """One entry of a ledger: what was asked, what came back, and its digest.

    ``result`` is the recorded value for the four reading kinds (``read_text``,
    ``now_ms``, ``random_seed``, ``random``, ``env``) so replay can feed it back,
    and ``None`` for ``write_text``, whose text is kept as ``result_sha256``
    alone.  ``args`` is the call as it was made, with paths already made relative
    to the run's ``effects_root``.
    """

    kind: str
    args: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    result_sha256: str = ""

    def as_entry(self) -> dict[str, Any]:
        """This entry as the run record carries it (``viewer/RECORD.md``)."""
        return {
            "kind": self.kind,
            "args": dict(self.args),
            "result": self.result,
            "result_sha256": self.result_sha256,
        }


def _entry(value: "Effect | Mapping[str, Any]") -> Effect:
    """One recorded entry, whether it came from a Receipt or from a JSON record."""
    if isinstance(value, Effect):
        return value
    if not isinstance(value, Mapping):
        raise EffectRefused(f"a recorded effect must be an entry object, got {type(value).__name__}")
    return Effect(
        kind=value.get("kind", ""),
        args=dict(value.get("args") or {}),
        result=value.get("result"),
        result_sha256=value.get("result_sha256", ""),
    )


class _Handle:
    """What :class:`Effects` and :class:`ReplayEffects` share: a root and a ledger."""

    __slots__ = ("_root", "_ledger")

    def __init__(self, root: str) -> None:
        if not root:
            raise ValueError(
                "an Effects handle needs an effects_root: every path it records is "
                "relative to that root, and a handle without one could only record "
                "absolute paths"
            )
        self._root = os.path.abspath(root)
        self._ledger: list[Effect] = []

    @property
    def root(self) -> str:
        """The absolute root.  It is never recorded; only paths relative to it are."""
        return self._root

    @property
    def ledger(self) -> tuple[Effect, ...]:
        """Every effect this handle has performed or replayed, in order."""
        return tuple(self._ledger)

    def entries(self) -> list[dict[str, Any]]:
        """The ledger as record entries (``viewer/RECORD.md``, ``effects``)."""
        return [effect.as_entry() for effect in self._ledger]

    def _relative(self, path: str) -> str:
        """``path`` as the ledger records it: relative to the root, with ``/``.

        An absolute path, or one that climbs out of the root, is refused: the
        ledger's whole claim is that it replays somewhere else, and a path
        outside the root does not.
        """
        if not isinstance(path, str) or not path:
            raise ValueError("an effect path must be a non-empty string")
        full = os.path.normpath(os.path.join(self._root, path))
        relative = os.path.relpath(full, self._root)
        if relative == os.pardir or relative.startswith(os.pardir + os.sep):
            raise ValueError(
                f"effect path {path!r} escapes the effects_root; every path an "
                "Effects handle touches is recorded relative to that root and must "
                "stay under it"
            )
        return relative.replace(os.sep, "/")

    def _full(self, relative: str) -> str:
        return os.path.join(self._root, relative.replace("/", os.sep))


class Effects:
    """The handle an ``oc.`` Calculation is called with; it performs and records.

    One handle per invocation, so ``Receipt.effects`` is that invocation's ledger
    and nobody else's.  Every method appends exactly one entry -- except the first
    ``random``, which appends the seed it drew and then the draws, because the
    seed is an effect too.
    """

    __slots__ = ("_handle", "_generator", "_seed_source")

    def __init__(self, root: str, *, seed_source: Any = None) -> None:
        self._handle = _Handle(root)
        self._generator: _random.Random | None = None
        # Injectable so a test can pin the seed without pretending the seed is
        # not an effect: it is still recorded, and still fed back on replay.
        self._seed_source = seed_source

    @property
    def root(self) -> str:
        return self._handle.root

    @property
    def ledger(self) -> tuple[Effect, ...]:
        return self._handle.ledger

    def entries(self) -> list[dict[str, Any]]:
        return self._handle.entries()

    def _record(self, kind: str, args: dict[str, Any], result: Any, digest_of: Any) -> Effect:
        effect = Effect(kind=kind, args=args, result=result, result_sha256=effect_digest(digest_of))
        self._handle._ledger.append(effect)
        return effect

    # --- the five verbs -------------------------------------------------------

    def write_text(self, path: str, text: str) -> str:
        """Write ``text`` at ``path`` under the root; record the path and the digest.

        Returns the recorded (relative) path, so a Calculation can publish where
        it wrote without knowing where the root is.
        """
        if not isinstance(text, str):
            raise ValueError(f"write_text needs text, got {type(text).__name__}")
        relative = self._handle._relative(path)
        full = self._handle._full(relative)
        os.makedirs(os.path.dirname(full) or self._handle.root, exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        self._record("write_text", {"path": relative}, None, text)
        return relative

    def read_text(self, path: str) -> str:
        """Read the text at ``path`` under the root; record the text and its digest."""
        relative = self._handle._relative(path)
        with open(self._handle._full(relative), encoding="utf-8") as stream:
            text = stream.read()
        self._record("read_text", {"path": relative}, text, text)
        return text

    def now_ms(self) -> float:
        """The wall clock in milliseconds -- an effect, and recorded as one."""
        value = time.time() * 1000.0
        self._record("now_ms", {}, value, value)
        return value

    def random(self, n: int) -> list[float]:
        """``n`` draws in ``[0, 1)`` from a seeded generator; the seed is an effect.

        The first call records the seed it drew (``random_seed``) before the
        draws, so the ledger carries everything a replay needs and nothing it has
        to guess.
        """
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise ValueError(f"random needs a non-negative count, got {n!r}")
        if self._generator is None:
            seed = self._seed_source if self._seed_source is not None else _random.SystemRandom().getrandbits(64)
            seed = int(seed)
            self._record("random_seed", {}, seed, seed)
            self._generator = _random.Random(seed)
        draws = [self._generator.random() for _ in range(n)]
        self._record("random", {"n": n}, draws, draws)
        return draws

    def env(self, name: str) -> str | None:
        """The environment variable ``name``, or ``None`` -- read once, recorded once."""
        if not isinstance(name, str) or not name:
            raise ValueError("env needs a non-empty variable name")
        value = os.environ.get(name)
        self._record("env", {"name": name}, value, value)
        return value


class ReplayEffects:
    """The same five verbs, answered from a recorded ledger instead of the world.

    Deterministic by construction: the same ledger produces the same answers in
    the same order, and its own ``ledger`` is the entries it replayed, so a
    replayed invocation's Receipt carries the effects the recorded one carried.

    The one effect that is re-performed is ``write_text``: the file is written
    again under this run's root and its digest compared with the recorded one, so
    a replay that would have written something else is refused rather than
    reported as equal.
    """

    __slots__ = ("_handle", "_recorded", "_index")

    def __init__(self, ledger: Iterable[Any], root: str) -> None:
        self._handle = _Handle(root)
        self._recorded: tuple[Effect, ...] = tuple(_entry(value) for value in ledger)
        self._index = 0

    @property
    def root(self) -> str:
        return self._handle.root

    @property
    def ledger(self) -> tuple[Effect, ...]:
        return self._handle.ledger

    def entries(self) -> list[dict[str, Any]]:
        return self._handle.entries()

    def remaining(self) -> tuple[Effect, ...]:
        """The recorded entries this replay has not consumed, in order."""
        return self._recorded[self._index :]

    def _next(self, kind: str, args: dict[str, Any]) -> Effect:
        index = self._index
        if index >= len(self._recorded):
            raise EffectRefused(
                f"replay refuses effect {index} ({kind}): the recorded ledger has "
                f"{len(self._recorded)} effect(s) and this run asked for one more"
            )
        recorded = self._recorded[index]
        if recorded.kind == kind and kind != "write_text":
            # The record is the disk here, so it is checked against itself before
            # anything is fed back: an entry whose result no longer digests to its
            # own `result_sha256` was edited after the run, and a replay that
            # returned it anyway would launder the edit into a fresh receipt.
            digest = effect_digest(recorded.result)
            if digest != recorded.result_sha256:
                raise EffectRefused(
                    f"replay refuses effect {index} ({kind}): the recorded result digests "
                    f"{digest} and the ledger claims {recorded.result_sha256}; an entry that "
                    "does not match its own digest was edited after the run that made it"
                )
        if recorded.kind != kind:
            raise EffectRefused(
                f"replay refuses effect {index} ({kind}): the recorded ledger has "
                f"{recorded.kind} at index {index}"
            )
        if dict(recorded.args) != args:
            raise EffectRefused(
                f"replay refuses effect {index} ({kind}): the recorded call is "
                f"{json.dumps(dict(recorded.args), sort_keys=True)} and this run asked "
                f"for {json.dumps(args, sort_keys=True)}"
            )
        self._index = index + 1
        self._handle._ledger.append(recorded)
        return recorded

    # --- the five verbs -------------------------------------------------------

    def write_text(self, path: str, text: str) -> str:
        """Re-write the file and refuse when the digest is not the recorded one."""
        if not isinstance(text, str):
            raise ValueError(f"write_text needs text, got {type(text).__name__}")
        relative = self._handle._relative(path)
        index = self._index
        recorded = self._next("write_text", {"path": relative})
        digest = effect_digest(text)
        if digest != recorded.result_sha256:
            # The entry is already consumed; the run stops here either way.
            raise EffectRefused(
                f"replay refuses effect {index} (write_text) at {relative!r}: the "
                f"recorded write digests {recorded.result_sha256} and this run would "
                f"write {digest}"
            )
        full = self._handle._full(relative)
        os.makedirs(os.path.dirname(full) or self._handle.root, exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        return relative

    def read_text(self, path: str) -> str:
        """The recorded text.  Nothing on disk is read: the record is the disk."""
        relative = self._handle._relative(path)
        return self._next("read_text", {"path": relative}).result

    def now_ms(self) -> float:
        """The recorded clock reading, in order."""
        return self._next("now_ms", {}).result

    def random(self, n: int) -> list[float]:
        """The recorded draws, seed entry included, in the order they were made."""
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise ValueError(f"random needs a non-negative count, got {n!r}")
        pending = self.remaining()
        if pending and pending[0].kind == "random_seed":
            self._next("random_seed", {})
        return list(self._next("random", {"n": n}).result)

    def env(self, name: str) -> str | None:
        """The recorded value of ``name``; this process's environment is not read."""
        if not isinstance(name, str) or not name:
            raise ValueError("env needs a non-empty variable name")
        return self._next("env", {"name": name}).result
