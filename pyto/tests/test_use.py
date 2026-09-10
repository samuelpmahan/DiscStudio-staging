"""USE.md, executed.

`pyto/USE.md` is the page a person reads to learn the surface: the store, a Part,
a Calculation, a program, the record, PQL. Every ```python block in it is run
here in a fresh process and its stdout is compared **byte for byte** with the
```text block that follows it, so the document is true or this suite is red.

One test per block, named for the section it lives in, so a red test names the
paragraph that lies rather than "the docs". A block with no text block after it
is only required to exit 0.

The blocks run with `cwd` at the pyto root and with `-I` (isolated: no
PYTHONPATH, no user site), so a block imports the installed `pyto` and nothing
else, and every path it names is relative to the pyto root -- which
`test_the_document_names_no_absolute_path` keeps true.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest

PYTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE_MD = os.path.join(PYTO_ROOT, "USE.md")

FENCE = re.compile(r"^```(python|text)[ \t]*$", re.MULTILINE)
HEADING = re.compile(r"^##+[ \t]+(.*?)[ \t]*$", re.MULTILINE)


class Block:
    """One ```python block, the section it sits in, and its expected stdout."""

    def __init__(self, index: int, section: str, source: str, expected: str | None) -> None:
        self.index = index
        self.section = section
        self.source = source
        self.expected = expected

    @property
    def name(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", self.section.lower()).strip("_")
        return f"test_{self.index:02d}_{slug or 'block'}"


def read_use_md() -> str:
    with open(USE_MD, encoding="utf-8", newline="") as handle:
        return handle.read()


def fenced_blocks(text: str) -> list[tuple[str, str, int]]:
    """Every fenced ``python``/``text`` block as ``(language, body, offset)``.

    Offset is where the block's opening fence starts, which is all the section
    lookup needs. Fences are matched in order and a body ends at the first line
    that is exactly ``` -- the blocks in USE.md hold no nested fences.
    """
    blocks: list[tuple[str, str, int]] = []
    position = 0
    while True:
        opened = FENCE.search(text, position)
        if opened is None:
            return blocks
        body_start = opened.end() + 1
        closed = text.find("\n```", opened.end())
        if closed < 0:
            raise AssertionError(f"USE.md has an unterminated ``` block at offset {opened.start()}")
        blocks.append((opened.group(1), text[body_start:closed + 1], opened.start()))
        position = closed + len("\n```")


def section_at(text: str, offset: int) -> str:
    """The nearest ``##`` heading above ``offset``."""
    name = "preamble"
    for heading in HEADING.finditer(text):
        if heading.start() > offset:
            break
        name = heading.group(1)
    return name


def parse_blocks(text: str) -> list[Block]:
    """Every python block in document order, paired with the text block after it."""
    fenced = fenced_blocks(text)
    blocks: list[Block] = []
    for position, (language, body, offset) in enumerate(fenced):
        if language != "python":
            continue
        expected = None
        if position + 1 < len(fenced) and fenced[position + 1][0] == "text":
            expected = fenced[position + 1][1]
        blocks.append(Block(len(blocks) + 1, section_at(text, offset), body, expected))
    return blocks


def run_block(source: str) -> tuple[int, bytes, bytes]:
    """Run one block in a fresh isolated process with cwd at the pyto root."""
    environment = dict(os.environ)
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONHASHSEED"] = "0"
    environment.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory() as directory:
        script = os.path.join(directory, "use_block.py")
        with open(script, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(source)
        completed = subprocess.run(
            [sys.executable, "-I", script],
            cwd=PYTO_ROOT,
            capture_output=True,
            env=environment,
            timeout=300,
        )
    return completed.returncode, completed.stdout, completed.stderr


BLOCKS = parse_blocks(read_use_md())

#: The one file on disk USE.md reads. It is the record section 5's own block produces.
FIXTURE = "tests/fixtures/use/order-record.json"
#: Where section 5's block stops building the record and starts reading the fixture back.
FIXTURE_SEAM = "# What a process that never saw the program above"


def write_fixture() -> str:
    """Regenerate FIXTURE from section 5's own block: ``python tests/test_use.py --write-fixture``.

    The fixture carries ``calculation.implementation_sha256``, the digest of the
    block's function bodies, so editing that block in USE.md is meant to turn this
    suite red until the fixture is written again -- and this is the one line that
    writes it, from the document itself rather than from a copy of the program.

    The block is cut at FIXTURE_SEAM (everything above it builds ``record``; below
    it the block reads the fixture that does not exist yet) and an epilogue is
    appended. Appending lines cannot change any function's source text, so the
    digests in the fixture are the digests of the block as written.
    """
    block = next((one for one in BLOCKS if one.section.startswith("5.")), None)
    if block is None or FIXTURE_SEAM not in block.source:
        raise SystemExit(f"USE.md has no record section with the seam {FIXTURE_SEAM!r}")
    head, _, _ = block.source.partition(FIXTURE_SEAM)
    epilogue = f'from pyto.materialize import write_record\nwrite_record(record, "{FIXTURE}")\n'
    code, out, err = run_block(head + epilogue)
    if code != 0:
        raise SystemExit(err.decode("utf-8", "replace"))
    return os.path.join(PYTO_ROOT, FIXTURE)


class UseMarkdownIsExecuted(unittest.TestCase):
    """Generated below: one test method per ```python block in USE.md."""

    def check(self, block: Block) -> None:
        code, out, err = run_block(block.source)
        detail = err.decode("utf-8", "replace")
        self.assertEqual(
            code, 0, f"USE.md section {block.section!r} block {block.index} failed:\n{detail}"
        )
        if block.expected is None:
            return
        self.assertEqual(
            out.decode("utf-8", "replace"),
            block.expected,
            f"USE.md section {block.section!r} block {block.index} prints something "
            "other than the text block under it",
        )
        self.assertEqual(out, block.expected.encode("utf-8"), "byte-for-byte comparison")


def _method(block: Block):
    def test(self: UseMarkdownIsExecuted) -> None:
        self.check(block)

    test.__name__ = block.name
    test.__doc__ = f"USE.md section {block.section!r}, block {block.index}."
    return test


for _block in BLOCKS:
    setattr(UseMarkdownIsExecuted, _block.name, _method(_block))


class UseMarkdownIsPortable(unittest.TestCase):
    """The document must read the same on any checkout, on any machine."""

    #: A path starting at the filesystem root, or a Windows drive letter.
    ABSOLUTE = re.compile(r"""(?:^|[\s"'(=`])(/[A-Za-z_.][\w./-]*|[A-Za-z]:[\\/])""")
    #: Anything that would put a machine's scratch space into the document.
    TEMPORARY = re.compile(
        r"/tmp\b|/var/folders|\btempfile\b|\bmkdtemp\b|\bmkstemp\b|"
        r"\bTemporaryDirectory\b|%TEMP%|\$TMPDIR\b",
        re.IGNORECASE,
    )

    def setUp(self) -> None:
        self.text = read_use_md()

    def test_the_document_names_no_absolute_path(self) -> None:
        found = [match.group(1) for match in self.ABSOLUTE.finditer(self.text)]
        self.assertEqual(found, [], "USE.md names an absolute path; every path must be relative")

    def test_the_document_names_no_temp_dir(self) -> None:
        found = sorted({match.group(0) for match in self.TEMPORARY.finditer(self.text)})
        self.assertEqual(found, [], "USE.md reaches for a temp directory; blocks must not")

    def test_every_block_has_its_output(self) -> None:
        """Every block in USE.md is pinned; a bare block would be a claim nobody checks."""
        unpinned = [block.index for block in BLOCKS if block.expected is None]
        self.assertEqual(unpinned, [], "these USE.md python blocks have no ```text block after them")

    def test_the_sections_are_the_ones_the_page_promises(self) -> None:
        self.assertEqual(
            [block.section for block in BLOCKS],
            [
                "1. The store",
                "2. A Part",
                "3. A Calculation",
                "4. A program",
                "5. The record",
                "6. PQL",
                "8. What not to do",
            ],
        )


if __name__ == "__main__":  # pragma: no cover - `python tests/test_use.py --show`
    if "--write-fixture" in sys.argv:
        print("wrote", write_fixture())
    elif "--show" in sys.argv:
        for block in BLOCKS:
            code, out, err = run_block(block.source)
            print(f"===== block {block.index} [{block.section}] exit {code}")
            sys.stdout.write(out.decode("utf-8", "replace"))
            if err:
                sys.stdout.write(err.decode("utf-8", "replace"))
    else:
        unittest.main()
