# Task 52

Intent: the surface a person uses: pyto/USE.md is a quickstart for PxC, Parts, Calculations, PCR and PQL that a test executes block by block and compares printed output byte for byte, so the document is true or the suite is red; the ergonomics gaps it exposes in pql.py and the top-level exports are fixed or written down; the students homework is its worked example
Starting point: 1eb5be232b32fb7f17591b9c6546b5f79f8f9810 (board: **measured** on MAIN after `task-39` landed, by the session, not a copy:)
Verify: cd pyto && python3 -m unittest tests.test_use tests.test_pql tests.test_first_class tests.test_semantics
Allow: pyto/USE.md pyto/README.md pyto/src/pyto/pql.py pyto/tests/test_use.py pyto/tests/test_pql.py pyto/tests/fixtures/use pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} AddressModuleNotExported: `USE.md` section 1 teaches the three roots, and the only code that
knows them lives in a module the package does not export: the block has to say
`from pyto.address import ROOTS, check` while everything else on the page comes from `from pyto
import ...`. `__init__.py` is another team's file this task may not edit. Export `ROOTS`,
`RESERVED_SECOND` and `check`, or leave the address rule a submodule import on purpose?

{?} MaterializeNotExported: same shape, and this one is on the main path -- the record is section 5
of a six-section quickstart, and reaching it reads `from pyto.materialize import run_record` and
`from pyto.px import main` after five sections of `from pyto import ...`. `run_record`,
`write_record` and the `px` entry point are the last step of every program that wants testimony;
`__init__.py` exports neither.

{?} PqlReceiptsIsNotAPQL: every other PQL constructor returns a `PQL` you can refine --
`PQL.prefix("px.").where(...)` -- but `PQL.receipts(pxc, pcr="order")` is a staticmethod that
takes the store and returns the matches, so narrowing receipts further is
`[m for m in PQL.receipts(pxc, pcr="order") if ...]` and not `.where(...)`. Split it into a
selector (`PQL.receipts_of(pcr=..., tick=...) -> PQL`) with `receipts(pxc, ...)` kept as the
one-liner, or leave the asymmetry?

{?} ReceiptConsumesHideResultReads: in `USE.md` section 3 the invocation `split` binds
`px.order.subtotal`, which `sum` published in the same run, and its receipt reports
`declared_consumes == ()` and `actual_consumes == ()` -- the read was resolved from the result,
not from the store. The run record does say so (`inputs: {"subtotal": "fn:sum"}`), and
`px.py:reads_of` unions the two sources to answer "what did this read". A reader looking at a
`Receipt` alone cannot. Is `declared_consumes` meant to be store reads only (then the page should
say it once, as it now does), or should a result read appear there as `fn:<id>`?

{?} HavenBriefSaysOneResult: `research/haven-brief.md:41-44` still defines a Calculation as taking
one mapping and returning "one result", which the kernel stopped meaning when `into=[...]` landed
({?} WhatIsATick, owner 2026-09-10). `USE.md` section 3 says one *or several* and shows both.
`research/` is outside this task's allow list, so the brief is left as it stands.

{?} UseMdFixtureRegeneration: `tests/fixtures/use/order-record.json` is the document section 5's
own block writes, and it carries `calculation.implementation_sha256` -- the digest of that block's
function bodies -- so editing the whitespace of `add_up` or `split_bill` in USE.md turns
`tests.test_use` red until the fixture is written again. That is the intended loudness, and the
regeneration is `python tests/test_use.py --write-fixture` (it cuts section 5's block at the
`# What a process that never saw the program above` comment and appends a `write_record`, so the
digests are the digests of the block as written). It lives in the test because `px` has no write
side today. Is a fixture written by a `--flag` on a test module the right home, or should the `px`
shell learn to write a record it can already read?
