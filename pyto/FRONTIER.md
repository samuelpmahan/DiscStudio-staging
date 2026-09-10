# The frontier

Every candidate on the record, merged into adds. An add is one piece of the OS plus the feature
that shows it, or a few complementary pieces. Never a bare kernel change (owner, 2026-09-10, on
`pyto/questions.md` under Frontier). A task opens from an add; the add's name is the intent. Order
is by what is understandable next, not by number. When an add lands, move it to "Landed adds" with
its task ids; when a candidate is absorbed elsewhere, say where.

Each add lists: what you see when it lands; the pieces it merges (with where each came from);
the verifier that decides; and the size in tasks.

## Adds, in the order that reads best

### A. Parallel you can see

You see: the Tick viewer shows a Tick's Calculations side by side when they are parallel branches,
with the Tick's work and its latency printed under it, and the students record (four steps, one
parallel) is the demo page.

Merges: tick_laws reports Ticks by name, not index (task 29, `{?} TickReportsHaveNoNames`);
work versus critical path on the tick page (TicksAsCircuits, "a number before any parallel
execution exists"); the tick page plays parallel branches together instead of one after another
(task 16's play/pause/step, extended).

Verifier: the viewer suite plus `tick_laws.py --check` on the students record; a node test that the
students page renders the Stats Tick as two side-by-side blocks.
Size: one task. Allow: pyto/experiments/tick-laws, pyto/viewer, pyto/experiments/students/README.md.

### B. Several results, all the way through

You see: a Calculation that publishes two Parts shows two fingerprints in the run record and two
cards in the viewer, and the studio's PQL document can say `into: [a, b]` and run it.

Merges: per-produce digests in the record document, not only the receipt (task 27,
`{?} RecordProduceDigest`; rewrites every committed record, touches viewer fixtures); the site's
`readPql`/`invokePql` grammar for several `into` (task 30, `{?} PqlMultiProduceIsRefused`: today
refused by name); the viewer's part index credits each produce (task 27 did the adapters; the
page does not draw them yet).

Verifier: the record-schema suite, the viewer suite, `npm test` in the studio, evidence regenerated
with the experiments' own scripts.
Size: two tasks (record and viewer first; the site grammar second). Kernel semantics, so its own
tasks, not the self-improve loop.

### C. The receipts are queryable

You see: `px ps <record>` prints one line per invocation from a record in a terminal without a
browser, and the studio's Inspect page lists its own receipts from `px.receipt.*` through PQL.

Merges: receipts as Parts (task 22, landed: `px.receipt.<pcr>.<tick>.<invocation>`); the Day 3
queue item "a text `px ps` over a record" (BOARD, 2026-09-09 09:20, never opened); the studio's
run-record export (task 21, landed) as the source; `{?} ReceiptInputNotRefused` and
`{?} ReceiptRerunOverwrite` from task 22's packet get a decision on the way (a receipt may be an
input; a rerun replaces, and the record keeps the run id).

Verifier: `python -m unittest tests.test_receipts` plus a new `px_ps` test on the students and
ablation records; the studio's browser check gains one check (raise the checkpoint count).
Size: one task for `px ps`, one for the studio page.

### D. A class in a repo

You see: a second repository holding one assignment (brief, verifier, reference, a sample
hand-off); a "student" desk in its own repo; `neat land <id> --from <desk> exp/<id> --verify <the
class's grader>`; the class board shows `landed task-N score 4/4 (from <desk>, graded here)`; and
the cold reader's answer, recorded beside the hand-off and compared.

Merges: NeatLearning (all the neat pieces landed: tasks 32, 33, 34); the students experiment (tasks
23, 29, 35); `{?}` from task 23, "where the cold reader's answer goes" (nothing records or scores
it today); the score line; private by default (the desk is its own repo).

Verifier: the class repo's own `check_all`; the selftest already proves the mechanics, so this add
is the first real trial rather than a script change.
Size: one task to make the assignment package and the trial script; the trial itself is the owner's
term with real students (Show Your Work, section 06).

### E. The student's own desk teaches the tutor

You see: a tutoring hand-off page generated from one student's desk: what they retried, where they
wrote `{?}`, what they undid, how long each Tick took them, drawn from their own records and never
from a profile.

Merges: Mounts (task 11, landed: a world above an ordinary PxC by an id outside the address space)
as the student's personal Part space; the `{?} Students` note "personal parts and calculations let
the agent learn how the student learns"; the landing receipts and undo receipts on the desk as the
source; the hand-off template (task 25's stopping rule) as the output shape.

Verifier: a test that the tutoring page is a pure function of the desk's receipts (same desk, same
page, byte for byte) and names no fact that is not in a receipt.
Size: one task after D.

### F. The workshop runs everywhere

You see: `proof.sh` green on Windows and on the Mac with the same receipt shape, and a landing that
edits `land.sh` itself lands cleanly.

Merges: `proof.sh` uses `mapfile` (bash 4) and macOS ships bash 3.2 (KT-MAC.md landmines); the
self-modifying landing hazard (task 34; the Mac debugs this by the owner's call: land.sh copies
itself to a temp file and re-execs before merging); the Windows proof already green.

Verifier: `proof.sh --selftest` on both shells, `neat selftest`, and a selftest check that lands a
change to `land.sh` in the scratch repo.
Size: one task, on the Mac.

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

- Ticks as circuits: tasks 26 (the laws), 27 (several produces), 29 (the students demo), 30 (the
  readers). The first add built the frontier way, before the method had a name.
- The board says what starts: tasks 24, 28, 31, 34 (started lines, loud refusals, the page, typed
  interrupts).
- neat-learning mechanics: tasks 32, 33, 34, 35 (score, land from a remote, graded here, exact
  hand-off lines).
- The Mac path: task 36 (KT-MAC.md).
