# Task 74: crisp: the owner, 2026-09-10: 'Like neat(not) and tidy, it has a TINY job it does VERY well. It does template gen that is required to import into PxC-ore and is tunable to imply or force decomposition. Variation through PxC is key.' pyto/src/pyto/crisp.py: crisp template <capability> [--mode imply|force] emits one composition proposal (capabilityDelta, why, existing and proposed Parts and Calculations, the PQL in the readPql shape, inspection, verification, decisions, limits) as a Part proposal.neat.composition.<set>.<option>.<revision> with a digest, from a store and a registry; imply leaves {?} slots, force refuses any name that does not resolve and any backwards read; crisp vary makes the options by changing one binding (variation A) or substituting one Calculation with the same produce shape (variation B), each option its own Part; crisp import runs a proposal's PQL against the registry and writes its Parts into the store with a run record; same inputs same bytes

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Stop here first (the owner's rule)

Read this page, `pyto/BOARD.md`, and the packet. No fourth file yet. Then write the one question
you would answer by reading another hundred thousand tokens of code, and ask the owner instead.
His answer is worth more than the reading: the last session that read everything first was
confidently wrong about half of it, and one sentence from him undid each wrong half. The answer
goes on `pyto/questions.md` verbatim, as `{?} Label: ...` with his words, so the next agent starts
one stupid question deeper. Only then read further and do the work below.

## Get the code (once)

```
git clone -b claude/os-sprint-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/74
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/74:pyto/experiments/tasks/74/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff bf7761d origin/exp/74 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
```

## Why this repository is worth twenty minutes

pyto is a Python transfer of a design the owner proved three times in JavaScript and TypeScript
(ChainSpot, ChessLab, EmbodiedWumpusWorld): a store of named values (PxC), pure functions over them
(Calculations), and a program that names which functions run in which order (a PCR, made of Ticks).
Every run leaves receipts: what each function read and wrote, how long it took, and a digest of its
source. From receipts you get three things for free: a cache (same inputs and digest, skip the call,
also across processes), a replay that verifies a shipped record in a fresh process, and a per-Tick
view of what the algorithm used. The founding need is the last one: the owner's course-map parser
had to fit five seconds on a phone, and nothing it used was visible. pyto is the workshop where that
visibility is designed before it is stripped for speed. JavaScript is first class; Python is where
the design is checked.

Do not take that from this page. In two minutes:

```
bash pyto/scripts/check_all.sh                                        # nine suites, ~600 tests
python pyto/experiments/grouped-ablation/run_cached.py --out /tmp/hit  # a miss, then two hits, one from a fresh process
node pyto/viewer/embed.mjs pyto/viewer/fixtures/pyto-grouped-ablation.json --out /tmp/hit/ticks.html
```

The tests were checked by mutation (each guards a specific line). The fixtures for the JavaScript
port are 440 byte-exact cases. `pyto/questions.md` is where anyone unsure writes `{?} Label: ...`
and the owner answers; read it before assuming. `pyto/BOARD.md` is the owner's one page.

## What was asked

crisp: the owner, 2026-09-10: 'Like neat(not) and tidy, it has a TINY job it does VERY well. It does template gen that is required to import into PxC-ore and is tunable to imply or force decomposition. Variation through PxC is key.' pyto/src/pyto/crisp.py: crisp template <capability> [--mode imply|force] emits one composition proposal (capabilityDelta, why, existing and proposed Parts and Calculations, the PQL in the readPql shape, inspection, verification, decisions, limits) as a Part proposal.neat.composition.<set>.<option>.<revision> with a digest, from a store and a registry; imply leaves {?} slots, force refuses any name that does not resolve and any backwards read; crisp vary makes the options by changing one binding (variation A) or substituting one Calculation with the same produce shape (variation B), each option its own Part; crisp import runs a proposal's PQL against the registry and writes its Parts into the store with a run record; same inputs same bytes

## Starting point

bc4d45c266d6de1d0ee1de7a207160854d5da81b (land(task-73): the Tick is the thing a person compares: px tick <record> [<name>] prints one Tick's projection of the record in the LAB's receipt shape (consumes, produces, writes with their kinds, frozen Calculations with source digests, latency, mode), byte-stable; px diff compares Tick by Tick before invocation by invocation and says which Ticks differ and in what; the viewer's Tick card shows the same four facts at the top of each Tick; derived from the record, no kernel change, no record change). MAIN may have moved since: `git log --oneline bf7761d..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/USE.md
- M  pyto/scripts/neat.sh
- A  pyto/src/pyto/crisp.py
- A  pyto/tests/fixtures/crisp/out/blok.a1-ink.27d1370d2f90.json
- A  pyto/tests/fixtures/crisp/out/blok.a2-paper.ac5943d1f570.json
- A  pyto/tests/fixtures/crisp/out/blok.b1-coordinatesInverted.5c22d72a43d9.json
- A  pyto/tests/fixtures/crisp/out/blok.root.2d0d8a7337f2.json
- A  pyto/tests/fixtures/crisp/out/run.json
- A  pyto/tests/fixtures/crisp/out/store-after.json
- A  pyto/tests/fixtures/crisp/registry.py
- A  pyto/tests/fixtures/crisp/root.pql.json
- A  pyto/tests/fixtures/crisp/store.json
- A  pyto/tests/test_crisp.py
- M  pyto/tests/test_use.py

```
pyto/USE.md                                        | 178 ++++++
 pyto/scripts/neat.sh                               |  16 +-
 pyto/src/pyto/crisp.py                             | 708 +++++++++++++++++++++
 .../crisp/out/blok.a1-ink.27d1370d2f90.json        |  49 ++
 .../crisp/out/blok.a2-paper.ac5943d1f570.json      |  49 ++
 .../blok.b1-coordinatesInverted.5c22d72a43d9.json  |  49 ++
 .../fixtures/crisp/out/blok.root.2d0d8a7337f2.json |  49 ++
 pyto/tests/fixtures/crisp/out/run.json             |  97 +++
 pyto/tests/fixtures/crisp/out/store-after.json     |  18 +
 pyto/tests/fixtures/crisp/registry.py              |  63 ++
 pyto/tests/fixtures/crisp/root.pql.json            |  16 +
 pyto/tests/fixtures/crisp/store.json               |   6 +
 pyto/tests/test_crisp.py                           | 387 +++++++++++
 pyto/tests/test_use.py                             |   3 +
 14 files changed, 1686 insertions(+), 2 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_crisp` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.xMLNplx4lI) (evidence/check_all.txt)
    suite                         tests  status
    library                         402  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} RegistryInputNames: the packet says a registry may map address -> {"calculation": ..., "inputs": [...]} but not how "inputs" lines up with a skeleton's matched Parts when there are several of each. I filled a shared cursor positionally, in matched-address order, across every matched Calculation in address order (documented in crisp.py's module docstring and exercised by the one-input, one-Part fixture); with two-plus inputs on one Calculation and an ambiguous pool this could bind the wrong Part to the wrong name and nothing would catch it.
{?} ValueKindKindOfCompat: Variation A groups by JSON type (number/string/list/mapping) per the packet's own words, so I used that literally. A kind match says nothing about the two values meaning the same thing (px.canvas.width could have been a number Part meant as a swatch id) -- it is the cheapest rule that fits the fixture, not necessarily the right one for a real store.
{?} OptionSlugSpelling: slugs are "a<n>-<last address segment>"/"b<n>-<last address segment>", derived to match the packet's own examples (a2-paper, b1-coordinatesInverted) exactly. The packet's own text also raised "whether option slugs should be digests" as an open question; I did not use the digest for the slug (only for the revision segment after it), since the address-derived slug is what made the given examples reproducible.
{?} ProduceShapeByInvocation: Variation B decides "same produce shape" by actually calling each candidate Calculation with the entry's own resolved inputs and counting the result -- the registry has no declared output count to compare against instead. This runs every fn. candidate in the registry once per vary; an oc. candidate is never invoked or offered, but a fn. candidate with a side effect disguised as purity would still run.
{?} ForceSkeletonRefusal: `crisp template --mode force` without `--pql` refuses outright ("force mode needs --pql") rather than trying to resolve a skeleton's "with" bindings and leaving "into" unresolved -- there is no way to invent an output address, and a half-resolved force skeleton felt worse than a clear refusal. Untested by any of the required tests either way.
{?} ProposedPartsFromInto: when deriving a proposal from a given --pql document, only "with" bindings and "call"s are classified as existing/proposed (the packet's literal rule); a Calculation's own new "into" outputs are never added to proposedParts, even though they are exactly the new behaviour capabilityDelta describes. They are still visible inside the embedded PQL, just not enumerated as their own proposedParts entries.
{?} VaryAlwaysClassifiesImply: `crisp vary`'s options are always built with the lenient (imply-style) with/call classification, regardless of whether the base proposal was made in imply or force mode, so a variant's existingParts/existingCalculations can never trip a refusal. This keeps vary simple and total, but a force-mode base's variants are not themselves re-verified against force mode's stricter rule.
{?} TestUseSectionListOutsideAllow: making `tests.test_use` green (this packet's own outer Verify line) required adding "9. crisp" three times to the hardcoded section list in `test_the_sections_are_the_ones_the_page_promises` (pyto/tests/test_use.py) -- a file this packet's Allow list does not name. I made the two-line edit rather than leave the suite red, since it is a literal enumeration of USE.md's own headings with no behaviour beyond that; the owner may prefer the test enumerate sections some other way, or to have this called out instead of changed.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 74 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 74`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-74): crisp: the owner, 2026-09-10: 'Like neat(not) and tidy, it has a TINY job it does VERY well. It does template gen that is required to import into PxC-ore and is tunable to imply or force decomposition. Variation through PxC is key.' pyto/src/pyto/crisp.py: crisp template <capability> [--mode imply|force] emits one composition proposal (capabilityDelta, why, existing and proposed Parts and Calculations, the PQL in the readPql shape, inspection, verification, decisions, limits) as a Part proposal.neat.composition.<set>.<option>.<revision> with a digest, from a store and a registry; imply leaves {?} slots, force refuses any name that does not resolve and any backwards read; crisp vary makes the options by changing one binding (variation A) or substituting one Calculation with the same produce shape (variation B), each option its own Part; crisp import runs a proposal's PQL against the registry and writes its Parts into the store with a run record; same inputs same bytes`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
