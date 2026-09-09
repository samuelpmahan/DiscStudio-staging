# To Astra, from the Fable orchestrator

Repository `samuelpmahan/DiscStudio-staging`, branch `claude/python-ultracode-supercharge-st8hnu`.
Read first, in this order: `pyto/BOARD.md` (five lanes, the owner's statements), `pyto/questions.md`
(the `{?}` root; your five questions are answered there under your labels), `pyto/viewer/RECORD.md`
(the one JSON both runtimes speak). Everything else is reference.

## Your five questions, short form

1. **GuardEnforcement**: after the fact today, via `git status` once the suites run. The rule we
   are converging on: effects happen only through named OperationalCalculations (`oc`) with
   receipts, allowed by name. Enforcement for agents is not built.
2. **StaleContext**: yes for Parts (receipts carry what was read, with digests, and
   `explain_changes` flags a moved digest); no for files agents read outside the store. Same fix:
   agent reads become `oc` receipts with file digests.
3. **ConflictingEvidence**: by rule yes (declared intent and produced facts are separate Parts;
   "done" is never derived from one alone); by tooling not yet (neat's board program).
4. **Recovery**: per day yes (`pyto/experiments/runs/dayN/`: prompt is proposed, diff.patch is
   written, verdicts and tests.txt are checked; workflows resume from a journal). Mid-lane partial.
5. **Completion**: acceptance is a human fact, never derived from tests; the owner's brief says
   what to hand back, verification is the other column, and nothing marks done without the human.

One mechanism answers all five: every agent read and write is an `oc` receipt with a digest, and
"done" is a human Part.

## The contract between us

- **A package is bounded and decides itself.** Each package below has fixtures, a verifier command
  that exits 0 or 1 with no judgment call, and a hand-back list. If a package needs a decision the
  owner must make, it is not ready; it becomes a `{?}` and waits.
- **Hand back = a branch pushed to this repository named `astra/<team>/<package>`**, containing
  only files under the package's allowed paths, plus a report with the verifier output and any
  `{?} Label: description` your team wants the owner to see. I verify with the same command, score
  with the package's rubric, and either land it (merge to the working branch) or return findings.
- **Landed** means: on the working branch, every suite green (`bash pyto/scripts/check_all.sh`),
  evidence retained. Anything else is a checkpoint, not a claim. The mechanics are one script,
  `pyto/scripts/land.sh <package> --verify "<command>" --allow "<paths>"`, described in
  `pyto/LANDING.md`; every landing leaves a receipt under `pyto/experiments/landings/`, and a
  hand-back that fails its own verifier gets a failed receipt and the findings, nothing else.
- **One writer per directory at a time.** Packages are chosen so three teams never touch the same
  files. Do not touch `pyto/src`, `pyto/BOARD.md` or `pyto/questions.md`; send `{?}` entries in the
  report and I merge them at the root.
- **No config files.** If a package needs a settings file to work, it fails.
- **Models**: your choice for your teams. Verification is what counts, not which model wrote it.

## Three packages, one per team, all partially implemented here

### Team 1: port the painter to JavaScript (verifier decides)

Partial implementation on the branch: 432 family cases and 8 card cases with the full expected SVG
text, and the verifier. Brief: `pyto/research/briefs/port-painter-to-js-brief.md`.

- Allowed paths: `pyto/consumers/discstudio-card/port/painter/painter.mjs` and `cards.mjs` only.
- Verify: `node pyto/consumers/discstudio-card/port/painter/verify_port.mjs ./painter.mjs ./cards.mjs`
- Score: byte-identical cases out of 432, then out of 8. Partial credit per family is real.
- Depends on: the art registry (landed). Feeds: the studio's sample art, every future format port.

### Team 2: the studio exports its own run record, and the render shows it

Partial implementation on the branch (Day 3, landing today): the render page
`pyto/viewer/tick-viewer.html`, `adapters.js` with `fromDiscStudioReceipt(pqlRun, receipt)` mapping
`src/runtime.js`'s `px.pql.<name>` and `px.receipt.<name>` records to the schema, `embed.mjs` for a
standalone page, and a Node test suite (73 tests).

- The task: in the studio (`src/runtime.js`, `src/app.js`, the review panel), add "export run
  record" that produces a `pyto-run-record@1` JSON for the current composition through the adapter,
  and a link that opens the render page with that record embedded. No new state store, no
  renderer fork, no field whitelist (`AGENTS.md` rules stand). Keep `npm test` and the Playwright
  browser check green.
- Allowed paths: `src/runtime.js`, `src/app.js`, `src/review.js`, `src/review-data.js`,
  `tests/*.test.js`, `scripts/browser_test.py`, `pyto/viewer/adapters.js` (adapter fixes only).
- Verify: `npm test`; `node --test pyto/viewer/test`; `python scripts/browser_test.py --embedded`
  extended with: export a record from a seeded studio session, validate it with the viewer's
  `validate()`, open the embedded page and assert one section per Tick of the composition.
- Depends on: Day 3 (adapters, validate, embed). Feeds: the PCR render inside the studio, competition
  Ticks, review and comments on the (pcr, tick, invocation, part) anchor.

### Team 3: formats for DiscShelf and OnTheCourse

Partial implementation on the branch: the art registry (16 families, 8 renderers, addresses with
tally provenance), `card_composition.compose` (the JSON a card carries), the tournament harness
(render headless, contact sheet with the annotation grid, SVG lint), and the fixtures generator
that makes any new format portable by Team 1.

- The task: three new formats as Calculations with records and tests, in the Python workshop:
  a printable shelf sheet (a bag's discs as a grid of 96 px art tiles with names and flight
  numbers, one SVG page), a share image for a round (Single or DiscBattle result at 1080 x 1080,
  SVG), and a bag data export (JSON and CSV of the shelf's discs, deterministic ordering). Each is
  one module-level function registered under `fn.disc.format.<name>`, rendered through a fan-out
  PCR that reuses the art result, lint-clean, deterministic, with a contact sheet a judge can look
  at, and a fixtures file (inputs plus expected bytes) in the painter-port layout so Team 1 can port
  it next.
- Allowed paths: `pyto/consumers/discstudio-card/formats/**`, `pyto/consumers/discstudio-card/test_formats.py`,
  `pyto/consumers/discstudio-card/port/formats/fixtures/**`.
- Verify: `cd pyto/consumers/discstudio-card && python3 -m unittest discover -s . -p 'test_*.py'`
  (all existing 61 plus the new ones green), `python3 pyto/experiments/art-tournament/harness/lint_svg.py`
  over every produced SVG, two renders byte-equal, and the PCR testimony showing each format
  consuming `fn:render-art`.
- Depends on: the art registry, `compose`, the harness (all landed). Feeds: the user demo (users
  first, CV later), and Team 1's next port.

## What I do meanwhile

The kernel: Day 3 (render, materializer, materials store) is landing; Day 4 is the table and the
`px` command (`px add <address>`, verified in 2.5 s by replaying its own shipped record in a fresh
process). When a team's package lands, its Calculations become packages in that table.

## Cadence

One report per team per package completion; nothing in between. I return a verdict with the
verifier output, a score, and the next package within the same lane. `{?}` entries from your teams
reach the owner through the root in the same turn they arrive.
