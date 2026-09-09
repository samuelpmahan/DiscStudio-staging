# The board

One file for the owner. Five lanes. Each lane has the current statement (one paragraph, the
latest refinement of everything said about it, older versions superseded), the prompts that are
open for the owner (three at most across the whole board, each with the default the agent takes
if unanswered), and where it stands. Agents append their own decisions to `questions.md`; the
status page is generated from this file. Nothing here needs to be re-read to catch up: read the
statements, answer the prompts, ignore the rest.

How the loop runs: the agent researches continuously in the background (subagents mine branches,
papers, the proven LABs) and writes findings that change a default as new prompts here; the owner
braindumps whenever they like, in any order, and the agent folds the dump into the lane
statements; overlapping ideas collapse into one statement per lane; silence past a prompt's
deadline means the default. The owner never has to keep track of more than this page.

## Lane 1: the kernel (this session owns it)

**Statement.** A portable AI kernel: PxC (five verbs: get, set, has, register, call) plus PCR and
Ticks as the sequencer, receipts as the trace, one JSON run record both runtimes read, and the PCR
render as the terminal. Namespaces are mount points; storage backends are chosen per mount by
that application's cold-start cost, measured, never configured; DuckDB (5.3 s) and OpenCV are out
of the runtime for that reason. JS is first class, Python is the workshop that replays, compares
and materializes the same records. Simple stays simple; extra effort earns its place. The demo
that justifies the week: `px add <address>`, verified in 2.5 seconds by replaying its own shipped
record in a fresh process. Verification is replay; there is no other kind.

**Open prompt.** *Addressing.* Each segment must discriminate and the root must connect. The
branch mining is reading `lab/pxc-root-mounts` and `review/pxc-root-alignment` for what was
already decided; the proposal returns with it. Default if unanswered: namespace first (`px` for
pixels, `disc`, `chess`, `wumpus`, `neat`, `tidy`), `fn.<namespace>` for Calculations, `?` for open
questions, no registration.

**Stands.** Days 1 and 2 landed (receipts, retain, fresh-process replay, second experiment with
zero program edits). Day 3 running (render, materializer, materials store). Day 4 queued (the
table and `px`). Day 5 planned (node reads the table, a JS skill verified, cross-project hit,
SUBDUE and WebShaper on recorded graphs).

## Lane 2: DiscStudio surfaces (Codex, briefed from lane 1)

**Statement.** Seed pyto's Python coverage in a set of interesting DiscStudio surfaces, chosen by
the propose-and-refine loop. Round four is on the table: addressing, PCR render, neat and tidy on
PxC, competition Ticks with proposals written to `proposal.disc.*` and promoted by a person, the
reducer in both runtimes, cards in the browser, review and comments on the (pcr, tick, invocation,
part) anchor, shelf statistics and export receipts. The tournament's sixteen families and eight
renderers are registered and waiting for the browser gate.

**Open prompt.** *Final surfaces list.* Reorder, cut, add. Default if unanswered: the round-four
list in that order.

**Stands.** Briefs written: Day 2 (as a bake-off reference), neat and tidy. Next brief: the PCR
render inside the studio, written once Day 3 returns the viewer's real API.

## Lane 3: neat and tidy (the owner's neat expert)

**Statement.** neat keeps work-item and git state as Parts in its own PxC so a change resolves
against that memory deterministically; one tree, no branch sprawl; the computer manages git.
Declared intent stays separate from produced facts; proposals never write into facts. neat's own
semantics (persistent PxC, total-order telemetry, failed runs return a result) are the reference
for neat. The neat agent runs this board: ingest dumps and research, resolve which questions got
answered and which lanes moved, propose the next prompts.

**Open prompt.** none. The brief is at `research/briefs/neat-on-pxc-brief.md` with five `{?}`
entries for the expert to bring back.

**Stands.** Brief handed off. Ticket storage is a different mount from the board render and is
not budget-bound.

## Lane 4: the record and the room (observability)

**Statement.** The founding need is seeing what the algorithm used, per Tick. A Tick is the unit
at which you are allowed to look. The run record carries values as material (JSON, text, SVG
rendered as an image, PNG data URLs), and the render shows per Tick what each Calculation read,
wrote, took, and whether it was a hit. Agents annotate on the anchor (pcr, tick, invocation, part)
plus a grid coordinate for images, so notes carry meaning rather than being dumb receipts. The
`{?}` root is where an agent says "I was confused here"; the owner answers; the answer stays.

**Open prompt.** *Should a saved run remember its commit?* It makes every record comparison
break on the next commit. Default if unanswered: remove the field; git and receipts already know.

**Stands.** Observability ledger written; Day 3 builds the render and the materializer.

## Lane 5: research comparisons

**Statement.** SUBDUE (Cook and Holder 1994) and WebShaper are engaged by mechanism, not slogan,
with primary sources on file; library learning (babble, LILO, ReGAL, SKILL-DISCO) is the nearest
published mechanism to promotion. The claim to defend is the promotion loop, compositions earning
names with evidence attached in a vocabulary the owner owns across projects, not the store.

**Open prompt.** none.

**Stands.** Sources collected; the executable comparison runs on Day 5 over recorded graphs.

## Decisions agents took with a default (no action needed)

Outputs never count as code changes for the dirty stamp. "Which inputs changed" lists anything
that differs. One writer per directory at a time. Pinned test counts are being removed. The
receipts seam decides nothing about the external-input boundary. Losers are kept, promotion is
reversible. Subagents run on Opus, Sonnet or Haiku at high effort. A hit is any use of a Part or
Calculation. Full list with reasons: `questions.md`.
