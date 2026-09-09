"""Mounts: a world is an id above an ordinary PxC, outside the address space.

The rule.  A world -- a course, a game, a bag -- is *mounted* under a root id
external to PxC's semantic address space: values stay ``px.*`` and calculations
stay ``fn.*`` inside every mounted world, and no address is ever rewritten to
carry the root.  A value at ``px.badges.px`` is reached only as
``mounts.get(root).get("px.badges.px")``; ``px.<root>.badges.px`` is never created
in any mounted PxC, so one address means one thing in every world.

The source is ``research/chainspot-branch-mining.md:36-88`` (section 2a), quoting
``43e6ea3:packages/alg/src/exec/mounts.ts:3-8`` for the rule ("The root is
intentionally external to PxC's semantic address space"), ``:11-22`` for the six
methods, ``:32-34``/``:40`` for the two loud errors, and
``43e6ea3:tests/unit/pxcRootMounts.test.ts:6-18`` for the negative test this port
keeps -- which section 6 item 1 (``:411``) calls the point: it "stops the LAB name
from creeping into addresses" (``questions.md:407-411``, ``{?} AddressRootIsAMount``).

The id is expected to be content-derived -- ChainSpot's is
``sha256(WxH:sha256(rgba))`` (``43e6ea3:.../operations.ts:688,707``), so same
material implies same root (``questions.md:413-416``, ``{?} RootIdIsContent``).
``Mounts`` does **not** compute it: the caller supplies the digest, and the human
label lives in a side map (``43e6ea3:scripts/warm-dev-pxc-roots.mjs:46-48``),
never in an address.  Reached as ``from pyto.mounts import Mounts``, which the
kernel does not import.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable

if TYPE_CHECKING:  # the runtime module has no dependencies at all
    from pyto.core import PxC

__all__ = ["Mounts"]


class Mounts:
    """Root ids above ordinary PxCs.  A root is never a segment of an address."""

    def __init__(self) -> None:
        self._mounted: dict[str, Any] = {}
        self._labels: dict[str, str] = {}

    def mount(self, root: str, pxc: PxC) -> None:
        """Mount a world beneath ``root``; re-mounting the same object is a no-op."""
        if not isinstance(root, str) or not root:
            raise ValueError("Mounts: a root id must be a non-empty str")
        current = self._mounted.get(root)
        if current is not None and current is not pxc:
            raise ValueError(f"Mounts: root '{root}' is already mounted")
        self._mounted[root] = pxc

    def has(self, root: str) -> bool:
        return root in self._mounted

    def get(self, root: str) -> PxC:
        """Return the exact PxC mounted at ``root``; no address rewriting occurs."""
        if root not in self._mounted:
            raise KeyError(f"Mounts: root '{root}' is not mounted")
        return self._mounted[root]

    def roots(self) -> tuple[str, ...]:
        """Stable insertion-order roots, for wide/grouped projection."""
        return tuple(self._mounted)

    def entries(self) -> tuple[tuple[str, PxC], ...]:
        """``(root, pxc)`` pairs in insertion order; the PxCs are the mounted ones."""
        return tuple((root, self._mounted[root]) for root in self._mounted)

    def slice(self, roots: Iterable[str]) -> Mounts:
        """A cheap root-level slice.  The mounted PxCs themselves are shared."""
        sliced = Mounts()
        for root in roots:
            sliced.mount(root, self.get(root))
            if root in self._labels:
                sliced.set_label(root, self._labels[root])
        return sliced

    def set_label(self, root: str, text: str) -> None:
        """Name ``root`` for a human.  The label lives here, never in an address."""
        if root not in self._mounted:
            raise KeyError(f"Mounts: root '{root}' is not mounted")
        self._labels[root] = text

    def label(self, root: str) -> str | None:
        """The label for ``root``, or ``None`` if it was never named."""
        if root not in self._mounted:
            raise KeyError(f"Mounts: root '{root}' is not mounted")
        return self._labels.get(root)
