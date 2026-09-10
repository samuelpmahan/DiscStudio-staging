# Task 75: crisp, second pass, what the owner settled today: two digests on every proposal, pnc over the Parts and Calculations only and review over structure, labels, prompt and candidates, so a label changes review and never pnc; crisp cards emits a set as Blok cards (root labelled, root unlabelled, each variant) with both digests; a binding may be live or pinned (address, or address plus sha256 that must match the store's value); an A-Star's known and unresolved seed the template's existing Parts and its {?} slots; and partness propagates instead of refusing: a Part computed from a part is a part, its receipt names its basis, force mode records a part binding as basis rather than refusing it, px ls shows provisional values with their basis, and the landing receipt counts provisional Parts; production is gated at promotion, never at binding

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
git fetch origin exp/75
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/75:pyto/experiments/tasks/75/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 5c8d3cc origin/exp/75 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

crisp, second pass, what the owner settled today: two digests on every proposal, pnc over the Parts and Calculations only and review over structure, labels, prompt and candidates, so a label changes review and never pnc; crisp cards emits a set as Blok cards (root labelled, root unlabelled, each variant) with both digests; a binding may be live or pinned (address, or address plus sha256 that must match the store's value); an A-Star's known and unresolved seed the template's existing Parts and its {?} slots; and partness propagates instead of refusing: a Part computed from a part is a part, its receipt names its basis, force mode records a part binding as basis rather than refusing it, px ls shows provisional values with their basis, and the landing receipt counts provisional Parts; production is gated at promotion, never at binding

## Starting point

f432097ec200503ed5fb299d900e958fad407316 (land(task-74): crisp: the owner, 2026-09-10: 'Like neat(not) and tidy, it has a TINY job it does VERY well. It does template gen that is required to import into PxC-ore and is tunable to imply or force decomposition. Variation through PxC is key.' pyto/src/pyto/crisp.py: crisp template <capability> [--mode imply|force] emits one composition proposal (capabilityDelta, why, existing and proposed Parts and Calculations, the PQL in the readPql shape, inspection, verification, decisions, limits) as a Part proposal.neat.composition.<set>.<option>.<revision> with a digest, from a store and a registry; imply leaves {?} slots, force refuses any name that does not resolve and any backwards read; crisp vary makes the options by changing one binding (variation A) or substituting one Calculation with the same produce shape (variation B), each option its own Part; crisp import runs a proposal's PQL against the registry and writes its Parts into the store with a run record; same inputs same bytes). MAIN may have moved since: `git log --oneline 5c8d3cc..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  .gitignore
- M  pyto/USE.md
- M  pyto/scripts/land.sh
- M  pyto/scripts/neat.sh
- M  pyto/src/pyto/crisp.py
- M  pyto/src/pyto/neat/gate.py
- M  pyto/src/pyto/px.py
- A  pyto/tests/fixtures/crisp/astar-blok.json
- D  pyto/tests/fixtures/crisp/out/blok.a1-ink.27d1370d2f90.json
- D  pyto/tests/fixtures/crisp/out/blok.a2-paper.ac5943d1f570.json
- D  pyto/tests/fixtures/crisp/out/blok.b1-coordinatesInverted.5c22d72a43d9.json
- D  pyto/tests/fixtures/crisp/out/blok.root.2d0d8a7337f2.json
- D  pyto/tests/fixtures/crisp/out/run.json
- D  pyto/tests/fixtures/crisp/out/store-after.json
- M  pyto/tests/test_crisp.py
- M  pyto/tests/test_neat_gate.py
- M  pyto/tests/test_px.py
- M  pyto/tests/test_use.py
- M  pyto/viewer/adapters.js

```
.gitignore                                         |   3 +
 pyto/USE.md                                        | 236 ++++++++-
 pyto/scripts/land.sh                               |  36 +-
 pyto/scripts/neat.sh                               |   6 +-
 pyto/src/pyto/crisp.py                             | 549 ++++++++++++++++++++-
 pyto/src/pyto/neat/gate.py                         |  27 +-
 pyto/src/pyto/px.py                                |  79 ++-
 pyto/tests/fixtures/crisp/astar-blok.json          |  16 +
 .../crisp/out/blok.a1-ink.27d1370d2f90.json        |  49 --
 .../crisp/out/blok.a2-paper.ac5943d1f570.json      |  49 --
 .../blok.b1-coordinatesInverted.5c22d72a43d9.json  |  49 --
 .../fixtures/crisp/out/blok.root.2d0d8a7337f2.json |  49 --
 pyto/tests/fixtures/crisp/out/run.json             |  97 ----
 pyto/tests/fixtures/crisp/out/store-after.json     |  18 -
 pyto/tests/test_crisp.py                           | 335 ++++++++++++-
 pyto/tests/test_neat_gate.py                       |  21 +
 pyto/tests/test_px.py                              |  44 ++
 pyto/tests/test_use.py                             |   3 +
 pyto/viewer/adapters.js                            |  50 +-
 19 files changed, 1364 insertions(+), 352 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_crisp tests.test_use tests.test_px tests.test_neat_gate` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.O9CNmLYpfT) (evidence/check_all.txt)
    suite                         tests  status
    library                         435  OK
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

{?} PncExcludesLabels: pnc's formula names "PQL" as one of its inputs, and a PQL document (`root.pql.json`) already carries its own top-level "labels" list beside "Ticks". Since the test requires a label to change review and never pnc, I read "PQL" in pnc's formula as `{"Ticks": ...}` only -- dropping "labels" (and any other top-level PQL key) before digesting for pnc, while review digests the value (and so the PQL, labels included) whole. If the owner meant something else by "PQL" in the pnc formula, this is the one place it would show.
{?} PinVerifiedOnlyAtImport: "Template and force mode accept both" (live/pinned) I read as accepting the syntax only; the actual sha256 check ("import resolves a pinned binding by checking...") I put solely in `crisp import`, never in `crisp template --mode force`. A proposal can therefore be written and inspected with a pin that no longer matches the store -- only import refuses it. If force-mode template building should also refuse a stale pin immediately, that is a small change to `build_pql_proposal`.
{?} PinDigestLength: a pin's `sha256` is accepted as either the full 64-hex digest or a short prefix of one (`_check_pins` compares by `startswith`), matching the "expected <12> got <12>" example in the packet, which shows 12-char values. I did not standardize on one length for the field itself (crisp's own `pins` writes carry whatever length the input gave, or the vary-substituted pin's fresh full digest) -- if pins should always be stored as exactly 12 hex, that's a one-line change.
{?} CardsNeedsStore: `crisp cards`'s CLI signature in the packet (`crisp cards <set-dir-or-proposal.json> --labels "..." [--out cards.json]`) has no `--store`, but "the exact input values from the store for its bindings" cannot be rendered without one, so I added `--store` as a required flag (matching template/vary/import's own style). Confirming this is fine, or that cards should instead read values already inside the proposal (it does not carry raw store values today, only value digests).
{?} CardsLabelsIsOneString: `--labels` takes one string, becoming the root labelled card's sole `labels` entry (`["<text>"]`); I did not split on comma, since the fixture's own example label ("One color, two representations") itself contains a comma. Repeating `--labels` for more than one label is not supported today.
{?} AstarNoPqlWiring: an A-Star study's `known` seeds `existingParts`/`existingCalculations` but I did not have it wire a Calculation invocation (the produced proposal's `PQL` carries one Tick with an empty `Calculations` list) -- A-Star intake reads as "what do we know and not know yet", with the wiring left to a follow-up `crisp vary`/hand edit, or a second `--pql` pass. If A-Star should also fill a skeleton-style "with" from its known Parts by declared input name, that is a related but separate addition.
{?} PartBasisIncludesTheRootItself: `px.part_basis`/crisp's `is_part` treat a root part address (`proposal.*`/`px.exp.*`) as standing on itself (`basis[addr] = {addr}`), so a part address that a run merely reads (never computed from another part) still shows `provisional (basis: <itself>)` in `px ls`. An alternative reading marks only *derived* addresses provisional and leaves a root part's own row as `-`; I judged the inclusive reading more useful (nothing under those two mounts should read as ordinary/production) and it is what the new `px.py`/`crisp.py` tests check.
{?} GateSelectionPncRequiredWhenSubjectHasPnc: when `subject.pnc` is set, `evaluate` now also refuses an event that carries no `selection_pnc` at all (treated the same as a mismatch), not only one that names a different pnc. If a human approval that simply doesn't mention pnc should still open the gate whenever the head sha matches, that check needs loosening.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 75 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 75`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-75): crisp, second pass, what the owner settled today: two digests on every proposal, pnc over the Parts and Calculations only and review over structure, labels, prompt and candidates, so a label changes review and never pnc; crisp cards emits a set as Blok cards (root labelled, root unlabelled, each variant) with both digests; a binding may be live or pinned (address, or address plus sha256 that must match the store's value); an A-Star's known and unresolved seed the template's existing Parts and its {?} slots; and partness propagates instead of refusing: a Part computed from a part is a part, its receipt names its basis, force mode records a part binding as basis rather than refusing it, px ls shows provisional values with their basis, and the landing receipt counts provisional Parts; production is gated at promotion, never at binding`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
