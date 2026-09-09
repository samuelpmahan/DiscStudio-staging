"""Tests for ``pyto.mounts``: the world is a mount id, never a segment.

Every test names, in its docstring, the one-line mutation it kills.  For all
but ``test_kernel_does_not_import_mounts`` -- which asserts the kernel stays
independent of this module -- that mutation is of ``src/pyto/mounts.py``; for
that one it is of ``src/pyto/core.py``, and for
``test_mounts_is_not_re_exported_from_the_package`` of ``src/pyto/__init__.py``.
Each mutation was applied one at a time, ``python -m unittest tests.test_mounts``
run, and the file restored; each named test failed on its own mutation --
21 of 21 killed.

The first class is the port of ChainSpot's negative test, "keeps ImgID outside
the PxC address space" (``43e6ea3:tests/unit/pxcRootMounts.test.ts:6-18``,
quoted at ``research/chainspot-branch-mining.md:56-65``), which section 6 item 1
(``research/chainspot-branch-mining.md:411``) says is the reason to port at all.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from pyto.core import Part, PxC
from pyto.mounts import Mounts

SRC = Path(__file__).resolve().parent.parent / "src" / "pyto"

BADGES = "px.s1.badges"


def _world(badges: list[str]) -> PxC:
    pxc = PxC()
    pxc.set(BADGES, badges)
    return pxc


class TestRootStaysOutsideTheAddressSpace(unittest.TestCase):
    def test_keeps_the_world_id_outside_the_pxc_address_space(self) -> None:
        """Kills: a prefix rewrite in ``mount`` -- ``for address in pxc.addresses():
        head, _, tail = address.partition("."); pxc.set(f"{head}.{root}.{tail}",
        pxc.get(address))`` inserted before ``self._mounted[root] = pxc``."""
        dash = _world(["dash"])
        north = _world(["north"])
        mounts = Mounts()
        mounts.mount("DashsTrack", dash)
        mounts.mount("NorthPark", north)

        # One semantic address, independently resolved in every mounted world.
        self.assertEqual(mounts.get("DashsTrack").get(BADGES), ["dash"])
        self.assertEqual(mounts.get("NorthPark").get(BADGES), ["north"])

        # The negative half: the root is never a prefix, anywhere.
        self.assertFalse(dash.has("px.DashsTrack.s1.badges"))
        self.assertFalse(north.has("px.NorthPark.s1.badges"))
        for root, pxc in mounts.entries():
            for address in pxc.addresses():
                self.assertNotIn(root, address, f"{root!r} leaked into {address!r}")

    def test_mounting_adds_no_address_at_all(self) -> None:
        """Kills: ``pxc.set("px.mount.root", root)`` inserted before
        ``self._mounted[root] = pxc`` in ``mount``."""
        dash = _world(["dash"])
        before = dash.addresses()
        Mounts().mount("DashsTrack", dash)
        self.assertEqual(dash.addresses(), before)
        self.assertEqual(before, (BADGES,))

    def test_get_returns_the_exact_object_mounted(self) -> None:
        """Kills: ``return copy.deepcopy(self._mounted[root])`` in ``get``."""
        dash = _world(["dash"])
        mounts = Mounts()
        mounts.mount("DashsTrack", dash)
        self.assertIs(mounts.get("DashsTrack"), dash)


class TestMountingIsIdempotentOrLoud(unittest.TestCase):
    def test_remounting_the_same_object_is_fine(self) -> None:
        """Kills: ``if current is not None:`` (dropping ``and current is not pxc``)."""
        dash = _world(["dash"])
        mounts = Mounts()
        mounts.mount("DashsTrack", dash)
        mounts.mount("DashsTrack", dash)
        self.assertEqual(mounts.roots(), ("DashsTrack",))
        self.assertIs(mounts.get("DashsTrack"), dash)

    def test_a_different_object_for_a_mounted_root_is_refused(self) -> None:
        """Kills: deleting the ``raise ValueError(... already mounted)`` branch."""
        mounts = Mounts()
        mounts.mount("DashsTrack", _world(["dash"]))
        with self.assertRaises(ValueError) as caught:
            mounts.mount("DashsTrack", _world(["other"]))
        self.assertIn("DashsTrack", str(caught.exception))
        self.assertEqual(mounts.get("DashsTrack").get(BADGES), ["dash"])

    def test_an_empty_root_is_refused(self) -> None:
        """Kills: deleting the ``if not isinstance(root, str) or not root:`` guard."""
        with self.assertRaises(ValueError):
            Mounts().mount("", PxC())
        with self.assertRaises(ValueError):
            Mounts().mount(None, PxC())  # type: ignore[arg-type]


class TestMissingRootIsLoud(unittest.TestCase):
    def test_get_of_a_missing_root_raises(self) -> None:
        """Kills: ``return self._mounted.get(root)`` in ``get``."""
        mounts = Mounts()
        mounts.mount("DashsTrack", PxC())
        with self.assertRaises(KeyError) as caught:
            mounts.get("NorthPark")
        self.assertIn("NorthPark", str(caught.exception))

    def test_has_reports_without_raising(self) -> None:
        """Kills: ``return True`` in ``has``."""
        mounts = Mounts()
        mounts.mount("DashsTrack", PxC())
        self.assertTrue(mounts.has("DashsTrack"))
        self.assertFalse(mounts.has("NorthPark"))

    def test_slice_of_a_missing_root_raises(self) -> None:
        """Kills: ``if not self.has(root): continue`` at the top of ``slice``'s
        loop -- skipping the missing root instead of raising."""
        mounts = Mounts()
        mounts.mount("DashsTrack", PxC())
        with self.assertRaises(KeyError) as caught:
            mounts.slice(["DashsTrack", "NorthPark"])
        self.assertIn("NorthPark", str(caught.exception))

    def test_labels_of_a_missing_root_raise(self) -> None:
        """Kills: deleting the ``if root not in self._mounted`` guard from
        ``set_label`` (a label for a root that was never mounted)."""
        mounts = Mounts()
        with self.assertRaises(KeyError):
            mounts.set_label("NorthPark", "North Park")
        with self.assertRaises(KeyError):
            mounts.label("NorthPark")


class TestRootsAndEntries(unittest.TestCase):
    def test_roots_keep_insertion_order(self) -> None:
        """Kills: ``return tuple(sorted(self._mounted))`` in ``roots``."""
        mounts = Mounts()
        for root in ("zulu", "alpha", "mike"):
            mounts.mount(root, PxC())
        self.assertEqual(mounts.roots(), ("zulu", "alpha", "mike"))
        mounts.mount("zulu", mounts.get("zulu"))
        self.assertEqual(mounts.roots(), ("zulu", "alpha", "mike"))

    def test_entries_pair_each_root_with_its_own_pxc_in_order(self) -> None:
        """Kills: ``for root in sorted(self._mounted)`` in ``entries``."""
        zulu, alpha = _world(["z"]), _world(["a"])
        mounts = Mounts()
        mounts.mount("zulu", zulu)
        mounts.mount("alpha", alpha)
        self.assertEqual(mounts.entries(), (("zulu", zulu), ("alpha", alpha)))
        self.assertEqual([root for root, _ in mounts.entries()], list(mounts.roots()))


class TestSliceSharesTheMountedObjects(unittest.TestCase):
    def test_a_write_through_a_slice_is_visible_through_the_original(self) -> None:
        """Kills: ``sliced.mount(root, copy.deepcopy(self.get(root)))`` in ``slice``."""
        dash, north = _world(["dash"]), _world(["north"])
        mounts = Mounts()
        mounts.mount("DashsTrack", dash)
        mounts.mount("NorthPark", north)

        sliced = mounts.slice(["DashsTrack"])
        self.assertEqual(sliced.roots(), ("DashsTrack",))
        self.assertIs(sliced.get("DashsTrack"), dash)

        sliced.get("DashsTrack").set(Part("px.s1.count"), 7)
        self.assertEqual(mounts.get("DashsTrack").get("px.s1.count"), 7)
        self.assertEqual(dash.get("px.s1.count"), 7)
        self.assertFalse(north.has("px.s1.count"))

    def test_slice_is_a_new_mounts_that_does_not_disturb_the_original(self) -> None:
        """Kills: ``sliced = self`` in place of ``sliced = Mounts()``."""
        mounts = Mounts()
        mounts.mount("DashsTrack", PxC())
        mounts.mount("NorthPark", PxC())
        sliced = mounts.slice(["NorthPark"])
        self.assertIsNot(sliced, mounts)
        self.assertEqual(mounts.roots(), ("DashsTrack", "NorthPark"))
        self.assertFalse(sliced.has("DashsTrack"))

    def test_slice_keeps_insertion_order_of_the_requested_roots(self) -> None:
        """Kills: ``for root in sorted(roots)`` in ``slice``."""
        mounts = Mounts()
        for root in ("zulu", "alpha", "mike"):
            mounts.mount(root, PxC())
        self.assertEqual(mounts.slice(["mike", "alpha"]).roots(), ("mike", "alpha"))


class TestLabelsStayOutOfAddresses(unittest.TestCase):
    def test_a_label_never_appears_in_any_address(self) -> None:
        """Kills: ``self._mounted[root].set("px.view.label", text)`` inserted
        before ``self._labels[root] = text`` in ``set_label``."""
        dash = _world(["dash"])
        mounts = Mounts()
        mounts.mount("a3f9c1", dash)
        before = dash.addresses()
        mounts.set_label("a3f9c1", "Dash's Track")

        self.assertEqual(mounts.label("a3f9c1"), "Dash's Track")
        self.assertEqual(dash.addresses(), before)
        for address in dash.addresses():
            self.assertNotIn("Dash", address)
            self.assertNotIn("a3f9c1", address)

    def test_an_unlabelled_mounted_root_has_no_label(self) -> None:
        """Kills: ``return self._labels.get(root, root)`` in ``label``."""
        mounts = Mounts()
        mounts.mount("a3f9c1", PxC())
        self.assertIsNone(mounts.label("a3f9c1"))

    def test_a_slice_carries_the_labels_of_the_roots_it_takes(self) -> None:
        """Kills: deleting the ``if root in self._labels: sliced.set_label(...)``
        lines from ``slice``."""
        mounts = Mounts()
        mounts.mount("a3f9c1", PxC())
        mounts.mount("b7e2d0", PxC())
        mounts.set_label("a3f9c1", "Dash's Track")
        sliced = mounts.slice(["a3f9c1", "b7e2d0"])
        self.assertEqual(sliced.label("a3f9c1"), "Dash's Track")
        self.assertIsNone(sliced.label("b7e2d0"))


class TestModuleStatus(unittest.TestCase):
    def test_kernel_does_not_import_mounts(self) -> None:
        """Kills: adding ``from pyto.mounts import Mounts`` to core.py."""
        for name in ("core.py", "pcr.py", "pql.py", "graph.py"):
            with self.subTest(module=name):
                text = (SRC / name).read_text(encoding="utf-8")
                self.assertNotIn("mounts import", text)
                self.assertNotIn("import mounts", text)

    def test_mounts_is_not_re_exported_from_the_package(self) -> None:
        """Kills: adding ``from .mounts import Mounts`` to ``__init__.py``."""
        import pyto

        self.assertNotIn("Mounts", pyto.__all__)
        self.assertFalse(hasattr(pyto, "Mounts"))

    def test_mounts_does_not_compute_the_root_id(self) -> None:
        """Kills: ``import hashlib`` plus ``root = hashlib.sha256(root.encode())
        .hexdigest()`` in ``mount`` -- ``{?} RootIdIsContent`` says the caller
        supplies the digest, so ``Mounts`` must not derive one."""
        text = (SRC / "mounts.py").read_text(encoding="utf-8")
        self.assertNotIn("hashlib", text)
        mounts = Mounts()
        pxc = PxC()
        mounts.mount("DashsTrack", pxc)
        self.assertEqual(mounts.roots(), ("DashsTrack",))
        self.assertIs(mounts.get("DashsTrack"), pxc)


if __name__ == "__main__":
    unittest.main()
