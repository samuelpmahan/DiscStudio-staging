# KT answers: five questions from the local session, answered by the cloud session

Asked through the owner on 2026-09-10 during the sprint. Answered from the record. Kept here so a
successor reads the mistakes, not only the decisions.

## 1. What evidence moved this from "function registry" to "AI Linux", and what is unproved

Four landings, in order. A receipt replayed byte for byte in a fresh process
(`pyto/experiments/grouped-ablation/evidence/replay/fresh-process.log`): the function stopped being
the unit; the receipt was. A cache hit by digest across processes (`run_cached.py`: one miss, two
hits, the second from a new process): a receipt became a durable object, which is what a file is.
Two runtimes reading one record (`pyto/viewer/RECORD.md`; the viewer and the materializer agree on
every fixture): a contract, which is what an ABI is. Receipts as Parts (task 22) and the circuit
laws checkable from receipts (task 26): everything is a Part, and the scheduler has an invariant a
script can verify.

Unproved: no scheduler ran before the sprint (task 39 is the first parallel executor); there is no
`oc`, so every Calculation is pure and an OS with no effects is a calculator; Mounts (task 11) exist
and nothing has mounted a world in production; digests drift between Python 3.11 and 3.14 (Codex's
Day 2 evidence, on the board, unresolved); macOS is unproven until the three-OS CI run (task 44)
finishes; the founding need, five seconds on a phone, was never measured against pyto; RBAC is a
design (NeatLearning) with no enforcement beyond git hosting.

## 2. Which of the owner's corrections overturned the most, and where the old assumptions survive

- "Codex never received it." I read a branch's author as its worker. The Today lines before the
  correction still say Codex delivered task 3; Lane 2's heading on the board still names Codex as
  its owner.
- "Was it ever said a Calculation could only have one result?" I promoted an API shape to a rule.
  `pyto/research/haven-brief.md` still says "returns one result"; RECORD.md's examples are all
  single `into`.
- "Reading is not depth." The hand-off template opens with the stopping rule and, two sections
  later, still hands over a reading list and a two-minute run; every BRIEF written for Codex was a
  reading list with no stopping rule, which is how the "actual consumes" error propagated (task 26).
- "You pushed an incorrect task." The habit survives in the sprint's team prompts, which assert
  facts about the record that were not re-checked (for example that the validator ignores unknown
  keys).
- "I shouldn't have to define an interrupt schema." Task 34's typed interrupts ([broke], [decision],
  [asked]) are one. Built rather than resolved.

## 3. Work called glue that holds a real method

- `write_packet_and_handoff` in `pyto/scripts/neat.sh`: candidate from merge base, diff, cold-start
  page. The reusable thing is the generator, not neat.
- `next_id` in neat.sh: reserving an id by pushing an empty branch is lock-free distributed
  allocation.
- CRLF normalization before hashing source (`pcr.py` `_implementation_sha256`, `retain.py`,
  `replay.py`): the portability rule for digests.
- `tick_laws._reads` (`pyto/experiments/tick-laws/tick_laws.py`): `fn:` refs resolved through
  `into`, one address or several, last-hash split: dependency extraction for any record.
- `grade.py` check 2 (`pyto/experiments/students/grade.py`): a standalone fresh-process replay
  harness with a stripped environment; the general replay method in two hundred lines.
- The selftest's scratch repository pair (neat.sh `cmd_selftest`): an integration-test method for
  any git workflow tool.
- The painter port's exact float formatting and MT19937 seeding
  (`pyto/consumers/discstudio-card/port/painter/core.mjs`) and the SUBDUE miner
  (`pyto/experiments/hiding-primitives/subdue.py`): real algorithms filed as experiments.
- The `fn:<id>#<address>` spelling with "known id wins, else split at the last hash": an algorithm
  living as a convention in `record_schema.py`, `adapters.js`, `compare_local.py`.

## 4. What a successor would follow correctly and still miss

- The test is the per-Tick page showing what each Calculation read and wrote with the value
  present, not a suite run. The three-OS CI pushes toward the wrong reading.
- Green names a receipt; refusals are evidence, kept, not failures to hide.
- The owner never types commands. KT-MAC blurs this by being commands for Codex.
- Questions are the product of understanding, not blockers to minimize (StoppingRule).
- Nothing is deleted: origin's `exp/*` branches are the record, not clutter.
- DiscStudio is the first tenant; the student on their own desk is the destination.
- The next test is not written anywhere. Proposed: a teacher grades a student's private desk from
  a different machine, with the tutor page rendered from that desk (frontier adds D and E).

## 5. When a question of the cloud session advanced the project

Almost never as a question. The productive form was a default with a reason, stated so it could be
overturned in one sentence: the three NeatLearning defaults got "private by default" back within a
minute; the three-line reading of what the owner wants got "Workspace. Educational." Open
questions were refused ("I shouldn't have to define an interrupt schema") or reframed
("philosophically, how do we launch something that gains depth"), and the reframing was the
advance. The question that moved the design most was not the cloud session's: a fresh agent under
the stopping rule asked what a Tick means to the watcher, and five landings followed (26 to 30).
