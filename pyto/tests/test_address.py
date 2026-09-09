"""Tests for ``pyto.address``: the round-five rule described, not enforced.

Every test names, in its docstring, the one-line mutation it kills.  For
sixteen of the seventeen that mutation is of ``src/pyto/address.py``; for
``test_kernel_does_not_import_address``, which asserts the kernel stays
independent of this module, it is of ``src/pyto/core.py``.  Each mutation was
applied one at a time to the file it names, the suite run, and that file
restored; each named test failed on its own mutation -- 17 of 17 killed.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from pyto.address import RESERVED_SECOND, ROOTS, Address, check, parse

SRC = Path(__file__).resolve().parent.parent / "src" / "pyto"


class TestRoots(unittest.TestCase):
    def test_roots_are_exactly_px_fn_oc(self) -> None:
        """Kills: ``ROOTS = ("px", "fn")`` -- dropping ``oc``."""
        self.assertEqual(ROOTS, ("px", "fn", "oc"))
        self.assertEqual(check("oc.disc.write"), ())

    def test_unknown_root_is_rejected(self) -> None:
        """Kills: ``elif False:`` in place of ``elif parsed.root not in ROOTS:``."""
        problems = check("scratch.exp.badges")
        self.assertTrue(problems, "a bare scratch root must be reported")
        self.assertIn("unknown root", problems[0])
        self.assertIn("scratch", problems[0])
        self.assertTrue(check("material.deadbeef"))
        self.assertTrue(check("matrix.material.key"))

    def test_known_roots_with_a_domain_noun_are_accepted(self) -> None:
        """Kills: ``ROOTS = ()`` -- refusing everything."""
        for address in ("px.badges.px", "fn.s1.exp.badgeAssembly.assemble",
                        "oc.fs.write", "px.shelf", "px.board.squares"):
            with self.subTest(address=address):
                self.assertEqual(check(address), ())


class TestSegments(unittest.TestCase):
    def test_empty_segment_is_rejected(self) -> None:
        """Kills: deleting the ``any(segment == "" ...)`` branch from check."""
        for address in ("px..badges", "px.badges.", "px."):
            with self.subTest(address=address):
                problems = check(address)
                self.assertTrue(problems)
                self.assertIn("empty segment", " ".join(problems))

    def test_leading_dot_is_rejected(self) -> None:
        """Kills: ``segments = tuple(address.strip(".").split("."))`` in parse."""
        parsed = parse(".px.badges")
        self.assertEqual(parsed.root, "")
        self.assertEqual(parsed.segments, ("", "px", "badges"))
        self.assertIn("empty segment", " ".join(check(".px.badges")))

    def test_empty_address_is_rejected(self) -> None:
        """Kills: ``return ()`` in place of ``return ("the address is empty",)``."""
        self.assertEqual(check(""), ("the address is empty",))
        self.assertEqual(parse("").segments, ())

    def test_bare_root_has_no_domain_noun(self) -> None:
        """Kills: deleting the ``if parsed.second is None:`` branch from check."""
        problems = check("px")
        self.assertTrue(problems)
        self.assertIn("second segment", " ".join(problems))
        self.assertIsNone(parse("px").second)

    def test_parse_splits_root_second_and_rest(self) -> None:
        """Kills: ``rest = segments[1:]`` in place of ``segments[2:]``."""
        parsed = parse("px.badges.px.detail")
        self.assertEqual(parsed.root, "px")
        self.assertEqual(parsed.second, "badges")
        self.assertEqual(parsed.rest, ("px", "detail"))
        self.assertEqual(parsed.segments, ("px", "badges", "px", "detail"))
        self.assertEqual(str(parsed), "px.badges.px.detail")


class TestReservedSecond(unittest.TestCase):
    def test_reserved_second_segments_are_the_six(self) -> None:
        """Kills: dropping ``"pql"`` from ``RESERVED_SECOND``."""
        self.assertEqual(
            RESERVED_SECOND,
            frozenset({"scratch", "view", "proposal", "run", "pql", "receipt"}),
        )

    def test_reserved_second_under_px_is_accepted(self) -> None:
        """Kills: dropping ``and parsed.root != "px"`` from the reserved branch."""
        for segment in sorted(RESERVED_SECOND):
            with self.subTest(segment=segment):
                self.assertEqual(check(f"px.{segment}.name"), ())

    def test_reserved_second_under_another_root_is_reported(self) -> None:
        """Kills: deleting the ``elif parsed.second in RESERVED_SECOND`` branch."""
        problems = check("fn.view.surface")
        self.assertTrue(problems)
        self.assertIn("reserved under px", " ".join(problems))


class TestOutsideTheAddressSpace(unittest.TestCase):
    def test_question_root_is_not_an_address(self) -> None:
        """Kills: deleting the ``if parsed.root == QUESTION_ROOT:`` branch."""
        problems = check("?.AddressRootIsAMount")
        self.assertTrue(problems)
        self.assertIn("outside the address space", " ".join(problems))

    def test_a_world_used_as_a_segment_is_not_detected(self) -> None:
        """Kills: adding a world blocklist (``if parsed.second in WORLDS``).

        The mount rule lives outside the text of the address, so ``check`` must
        not pretend to see it.
        """
        for address in ("px.chess.board", "px.disc.bag", "px.neat.task",
                        "px.wumpus.room", "px.tidy.rule"):
            with self.subTest(address=address):
                self.assertEqual(check(address), ())


class TestDescribesAndDoesNotEnforce(unittest.TestCase):
    def test_address_is_a_frozen_dataclass(self) -> None:
        """Kills: ``@dataclass`` in place of ``@dataclass(frozen=True)``."""
        parsed = parse("px.badges.px")
        self.assertIsInstance(parsed, Address)
        with self.assertRaises(Exception):
            parsed.root = "fn"  # type: ignore[misc]

    def test_module_imports_nothing_from_pyto(self) -> None:
        """Kills: adding ``from pyto.core import Part`` to address.py."""
        tree = ast.parse((SRC / "address.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn("pyto", node.module or "")
                self.assertEqual(node.level, 0, "no relative import of pyto")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertFalse(alias.name.startswith("pyto"))

    def test_kernel_does_not_import_address(self) -> None:
        """Kills: adding ``from pyto.address import check`` to core.py."""
        for name in ("core.py", "pcr.py", "pql.py"):
            with self.subTest(module=name):
                text = (SRC / name).read_text(encoding="utf-8")
                self.assertNotIn("address import", text)
                self.assertNotIn("import address", text)

    def test_parse_rejects_non_strings(self) -> None:
        """Kills: deleting the ``isinstance(address, str)`` guard in parse."""
        with self.assertRaises(TypeError):
            parse(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
