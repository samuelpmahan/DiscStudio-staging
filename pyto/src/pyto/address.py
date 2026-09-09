"""The round-five address rule, described and not enforced.

The rule, as recorded by the owner and the mining:

* Three roots only -- ``px`` (values), ``fn`` (pure calculations), ``oc``
  (effects) -- ``BOARD.md:100-102``, ``research/chainspot-branch-mining.md:170-172,182``.
  ``fn`` is the only root Python checks today (``src/pyto/core.py:33-34``); a
  Part's address is only checked for being non-empty (``src/pyto/core.py:17-19``),
  which is how bare ``scratch.`` and ``material.<sha>`` got in
  (``questions.md:125-129``).
* Six reserved second segments under ``px``: ``scratch``, ``view``,
  ``proposal``, ``run`` (``BOARD.md:103-104``, ``questions.md:352-353``), ``pql``
  (``questions.md:441-443`` ``{?} PqlRunRootStatus``) and ``receipt``
  (``questions.md:137-138``/``questions.md:548-551`` ``{?} EverythingIsAPart``).
  Any other second segment is the domain noun that outlives the stage that made
  it -- ``px.badges.px`` -- which is where connection lives
  (``research/chainspot-branch-mining.md:184``).
* A world (``disc``, ``chess``, ``wumpus``, ``neat``, ``tidy``) is a **mount**,
  outside the address and never a segment, so one address means one thing in
  every world (``BOARD.md:97-100``, ``research/chainspot-branch-mining.md:157``).
* ``?`` is the root of questions and provenance and is outside the address
  space (``research/chainspot-branch-mining.md:164,188``).

This module describes; it enforces nothing.  ``core.py``, ``pcr.py`` and
``pql.py`` do not import it and reject nothing because of it.  ``check`` reports
only what is visible in the string.  It can never report a world used as a
segment: a world name is an ordinary lowercase noun, and the mount rule lives
outside the text of the address (``research/chainspot-branch-mining.md:195-197``).
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ROOTS", "RESERVED_SECOND", "Address", "parse", "check"]

ROOTS: tuple[str, ...] = ("px", "fn", "oc")

RESERVED_SECOND: frozenset[str] = frozenset(
    {"scratch", "view", "proposal", "run", "pql", "receipt"}
)

QUESTION_ROOT = "?"


@dataclass(frozen=True)
class Address:
    """A dotted address split into its parts.  No validation happens here."""

    root: str
    second: str | None
    rest: tuple[str, ...]
    segments: tuple[str, ...]

    def __str__(self) -> str:
        return ".".join(self.segments)


def parse(address: str) -> Address:
    """Split ``address`` on ``.`` into root, second segment and the rest.

    An empty string parses to an empty ``Address``; empty segments (a leading
    or trailing dot, or ``..``) are preserved as empty strings so ``check`` can
    see them.
    """
    if not isinstance(address, str):
        raise TypeError("address must be a str")
    segments: tuple[str, ...] = tuple(address.split(".")) if address else ()
    root = segments[0] if segments else ""
    second = segments[1] if len(segments) > 1 else None
    rest = segments[2:]
    return Address(root=root, second=second, rest=rest, segments=segments)


def check(address: str) -> tuple[str, ...]:
    """Return plain-English violations of the round-five rule, in order.

    An empty tuple means nothing in the *string* violates the rule.  It does
    not mean the address is right: a world name used as a segment
    (``px.chess.board``) is indistinguishable from a domain noun
    (``px.badges.px``) and is never reported.
    """
    parsed = parse(address)
    problems: list[str] = []

    if not parsed.segments:
        return ("the address is empty",)

    if any(segment == "" for segment in parsed.segments):
        problems.append(
            "the address has an empty segment "
            "(a leading dot, a trailing dot, or two dots in a row)"
        )

    if parsed.root == QUESTION_ROOT:
        problems.append(
            "'?' is the root of questions and provenance, "
            "outside the address space; it is not an address root"
        )
    elif parsed.root not in ROOTS:
        problems.append(
            f"unknown root {parsed.root!r}: the only roots are "
            f"{', '.join(ROOTS)} (px for values, fn for pure, oc for effects)"
        )

    if parsed.second is None:
        problems.append(
            f"the address is a bare root with no second segment; "
            f"{parsed.root!r} needs the domain noun that outlives the stage "
            "that made it"
        )
    elif parsed.second in RESERVED_SECOND and parsed.root != "px":
        problems.append(
            f"second segment {parsed.second!r} is reserved under px "
            f"and is used here under {parsed.root!r}"
        )

    return tuple(problems)
