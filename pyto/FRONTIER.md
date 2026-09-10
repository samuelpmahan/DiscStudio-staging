# The frontier

Every candidate on the record, merged into adds. The owner, 2026-09-10, on `pyto/questions.md`
under `{?} Frontier`: "I think the best way to run this is to build whatever task frontier and
instead of going just in order we refine and merge compatible things. Building the OS is much more
understandable if each add includes an illustrative feature add or is a few complementary things."

So: an add is one piece of the OS plus the feature that shows it, or a few complementary pieces,
never a bare kernel change. A task opens from an add; the add's name is the intent. Order is by
what is understandable next, not by number. When an add lands, move it to "Landed adds" with its
task ids; when a candidate is absorbed elsewhere, say where. Everything below that is not quoted is
this session's description of what landed, not the owner's words.

Each add lists: what you see when it lands; the pieces it merges (with where each came from);
the verifier that decides; and the size in tasks.

## Adds, in the order that reads best

### F. The workshop runs everywhere (partly landed: tasks 44 and 46)

Landed already: a GitHub Action runs `check_all.sh` on ubuntu, macos and windows on every push to
the sprint branch (task 44), and task 46 made it green there on two Python versions and had it
upload the per-suite logs as the receipt. So the suite is proved on three operating systems by a
machine, not by a claim.

Still open, and both of them want the Mac itself:

You see: `proof.sh` green on the Mac with the same receipt shape it has on Windows, and a landing
that edits `land.sh` itself lands cleanly.

Merges: `proof.sh` uses `mapfile` (bash 4) and macOS ships bash 3.2, so today it needs
`brew install bash` and an explicit interpreter (KT-MAC.md landmines); the self-modifying landing
hazard (task 34; the Mac debugs this by the owner's call: land.sh copies itself to a temp file and
re-execs before merging), which nothing in the sprint touched.

Verifier: `proof.sh --selftest` on both shells, `neat selftest`, and a selftest check that lands a
change to `land.sh` in the scratch repo.
Size: one task, on the Mac. CI covers `check_all.sh` on three OSes; it does not run `proof.sh`.

### G. DiscStudio ships

You see: the shelf sheet and the painted card in the deployed site, Astra's package three (two
formats), and the card renderer question (`{?} CardRenderer`) answered by a default in the site.

Merges: Astra package one (landed) and the two remaining formats; Lane 2's format wiring; the
`{?} CardRenderer` default; the studio run-record export (task 21) as the debugging surface.

Verifier: `npm test`, the viewer suite, `browser_test.py --embedded`, the Pages build.
Size: one task per format when Astra hands back; nothing to open until then.

### H. The gate is a command

You see: `neat gate <id>` prints the cold-reader page, takes the reader's explanation from a file,
runs the judge, and writes the verdict as a receipt beside the task; the board line says
`gate passed` or `gate refused: <reason>`.

Merges: the explicability gate (LANDING.md; run by hand for task 9, refused once, passed on the
second read); `{?} DeterministicInterrupts`'s principle that judgment signs in before it has
effect; the hand-off template.

Verifier: the selftest runs the gate with a canned explanation that matches and one that does not.
Size: one task. The reader and judge stay models; the command is the accounting around them.

### I. One private monorepo

You see: one clone that is the whole lab: pyto, DiscStudio, ChainSpot, ChessLab, Wumpus as
folders with their history; one board, one root of questions, one id sequence; `proof.sh` proves
all of it.

Merges: the owner's question of 2026-09-10 ("a private monorepo would be most portable"); the
three id collisions; the bundle repo (BUNDLE.md); the work brain and student desks stay out by
the RBAC decision.

Verifier: `proof.sh` from a fresh clone of the monorepo.
Size: one careful task; the owner decides when.

## Candidates absorbed above (so nothing is lost)

Adds A to E landed in the sprint below and are no longer on this list; the arrows are kept as they
were written, so a candidate can still be traced to the add that took it.

- `{?} TickReportsHaveNoNames` (29) → A. `{?} TickLawsReadmeQuotesLiveMicroseconds` (29) → A.
- `{?} RecordProduceDigest`, `{?} SingleIntoReaders` (27; readers done in 30) → B.
- `{?} PqlMultiProduceIsRefused`, `{?} ConsumersOfOverlap`, `{?} PxWriterLastWins` (30) → B.
- `{?} ReceiptInputNotRefused`, `{?} ReceiptPreexisting`, `{?} ReceiptNameSegments`,
  `{?} ReceiptRerunOverwrite`, `{?} ReceiptStoreSetUnguarded` (22) → C.
- Day 3 queue: `px ps`, the `oc` syscall table prototype → C (`px ps`) and open (`oc`: stays a
  `{?}`, no add yet; it is a kernel semantic and needs its own illustrative feature first).
- Task 23's "where the cold reader's answer goes", `{?} MissingTickTest...` (closed in 35) → D.
- `{?} Students` personal Parts note → E.
- KT-MAC landmines, the land.sh hazard, `{?} ParkingIsManual` → F.
- `{?} CardRenderer`, Astra package three, Lane 2 → G.
- The gate run by hand, `{?} NeatFromVerify` (done in 34) → H.
- `{?} TaskIds`, `{?} FoldersNotBranches`, the bundle repo → I.
- UndoStack as a Part for the site (`{?} UndoStack`): open; it pairs with G once a format needs
  undo in the browser.

## Landed adds

The sprint of 2026-09-10 02:20 UTC, in the owner's words: "Now branch and build the most badass OS
out of this you possibly can. Make sure to push no less than once every ten minutes. No longer
worry about explanability: testable determinism is your guide. Use as many agents as you can in
OpusSonnetSonnet teams and plan ahead to merge and parallelize your frontier."

What that sprint landed, one line per add, named by the task's own intent line, with what you see:

- Parallel for real and budgets: task 39. A Tick's Calculations run at once when none of them reads
  another, each invocation says which worker ran it and when it started, and a run given a time
  budget stops at a Tick boundary with the record saying where it stopped -- and the testimony is
  the same bytes serial or parallel.
- Parallel you can see: task 40 (add A). The Tick page draws a parallel Tick's Calculations side by
  side, prints that Tick's work against its latency and the run's work against its critical path,
  and shows placement and an unfinished budget when the record carries them.
- The px shell: task 41 (add C, the terminal half). `px ps`, `px ls`, `px cat`, `px diff`,
  `px laws` and `px receipts` read a run record in a terminal with no browser, each one byte for
  byte the same twice, and the store now refuses a write under `px.receipt.` that is not a run's own.
- The studio speaks the whole record: task 42 (add B, the site half, and add C's studio half). The
  browser grammar takes several `into` per Calculation and runs it, the Inspect page lists the
  studio's own receipts through PQL, and the Shelf card has an Undo button whose push and pop are
  ordinary invocations the run record carries.
- A class in a repo and the desk that teaches the tutor: task 43 (adds D and E). One command builds
  a class repo and a student's private desk, plays both sides, and lands the desk into the class
  graded by the class's own verifier -- the board line is the gradebook -- and `tutor.py` renders
  that desk's own record as a page that is the same bytes on rerun and reads no profile.
- The suite runs everywhere it claims to: tasks 44 and 46 (add F, in part). A GitHub Action runs
  `check_all.sh` on ubuntu, macos and windows on every push to the sprint branch, and 46 made it
  green there on two Python versions and had it upload the per-suite logs as the receipt.
- KT answers: task 45. Five questions from the local session answered from the record, at
  `pyto/research/kt-answers.md`, with `START-HERE.md` pointing at them.
- neat never reuses an id: task 47. `next_id` counts the landing receipts as well, so an undone or
  killed task's number is never handed out again, and the selftest proves it.

- The JavaScript runtime speaks the same schedule: task 48 (add B's runtime half). `exec.js` runs a
  Tick's Calculations concurrently when the node law holds and refuses sibling reads at read time,
  takes a budget that stops at a Tick boundary, and the studio's run record carries `parallel`,
  `placement`, `latency_ms` and `budget` exactly as the Python kernel writes them; testimony
  byte-identical serial versus parallel; the studio's Tick page shows a parallel Tick.
- oc, effects with receipts: task 49 (the `oc` item the Day 3 queue left open). An
  OperationalCalculation (`oc.` prefix) may perform effects only through an Effects handle the run
  gives it (write_text, read_text, now_ms, random, env); every effect is recorded in the receipt and
  the run record; replay feeds recorded effect results back and refuses a tampered one; `fn.`
  Calculations get no effects; `px effects` lists them; testimony byte-identical observe on and off.
- Effects you can see and the sprint on the one page: task 50. The Tick viewer shows an
  invocation's effects (kind, path, digest) when the record carries them and draws `oc`
  Calculations distinctly; KT-MAC gains the px shell in chunk 3 and a classroom chunk 7; this file
  records the sprint's landed adds.
- CI runs to completion: task 51 (add F, in part). `check_all.yml` no longer cancels a run in
  progress when the next landing pushes, and skips pushes that touch only the board or the landing
  receipts, so every landing gets its three-OS receipt.
- The surface a person uses: task 52. `pyto/USE.md` is a quickstart for PxC, Parts, Calculations,
  PCR and PQL that a test executes block by block and compares printed output byte for byte, so the
  document is true or the suite is red; the students homework is its worked example.
- Green on macOS and Windows: task 55 (add F, in part). The three failures the three-OS run showed
  at a9e3b1a were the tests, not the kernel: test_use.py compared CRLF stdout on Windows to LF
  text, test_classroom.py spelled bash so Windows resolved WSL's instead of Git's, and
  test_parallel's overlap check gave four threads 50 ms to start where a slow macOS runner took
  114. Each test is made true on the platform it runs on without loosening what it proves.

- Chains inside a Tick: tasks 57 (the kernel), 58 (the laws, `px laws`, the readers and the viewer)
  and 59 (the studio's runtime), after the owner's correction of 04:05 ("'Calculations inside a Tick
  must be independent' was added as a rule, while your existing ChainSpot program deliberately chains
  dependent Calculations inside a Tick. Your definition was the moment that sequence becomes
  inspectable."). Inside a Tick the Calculations are a sequence in declared order and the Tick
  boundary is where it becomes inspectable; a Tick with no sibling reads may run at once; a read of
  a later sibling and two siblings producing one address are the refusals that remain. Decided on
  `pyto/questions.md` under ChainsInsideATick, in his words; the interrupt rule's veto beside it.
- The Mac's next three: task 61. KT-MAC.md's hand-off carries what the three-OS run showed after
  task 55, so the Mac session starts on facts, not on a green claim.
- Molecules, the owner's last call ("one last 30 min moonshot NOT OS. SUBDUE-PxC-PQL moonshot"):
  task 60. `pyto/experiments/molecules` mines the eight committed run records with the SUBDUE miner
  from hiding-primitives and names each repeated chain of Calculations over Parts a molecule, with
  the PQL document that spells it and the PQL query that finds its Parts; `report.md` rebuilds byte
  for byte and `--check` refuses drift. What it does not do yet: run an emitted document, or make a
  molecule a Calculation of its own (its packet's `{?}` lines).
- Decisions taken for the owner, to review: task 62, `pyto/research/decisions-to-review.md`, every
  default the session took in his place, verified against the record, each with the sentence that
  overturns it.

What those adds did not finish, so it is not lost with them:

- The record still carries one `result_sha256` per invocation and no per-produce digest
  (`{?} RecordProduceDigest`): adding the field rewrites the bytes of every record ever written.
- The viewer's DiscStudio reader still writes one `into` per invocation, so the studio's own
  multi-produce Calculation is not run-recorded (`{?} RecordAdapterHasOneIntoPerInvocation`, 42).
- A rerun replaces each receipt Part in place and the record has a `pcr` name but no run id, so
  add C's "the record keeps the run id" is not done (`{?} ReceiptRerunOverwrite`, 41).
- `neat undo <id>` freeing an id was worked around inside `make_class.sh` before task 47 fixed
  `next_id`; the workaround is still in that script (`{?} NeatUndoFreesTheId`, 43).

Before the sprint:

- Ticks as circuits: tasks 26 (the laws), 27 (several produces), 29 (the students demo), 30 (the
  readers). The first add built the frontier way, before the method had a name.
- The board says what starts: tasks 24, 28, 31, 34 (started lines, loud refusals, the page, typed
  interrupts).
- neat-learning mechanics: tasks 32, 33, 34, 35 (score, land from a remote, graded here, exact
  hand-off lines).
- The Mac path: task 36 (KT-MAC.md).
