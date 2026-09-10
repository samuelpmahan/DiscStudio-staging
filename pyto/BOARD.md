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

## The test

"We get AHI running on my local D:/ drive." AHI is Augmented Human Intelligence: human centric,
AI extends. The whole loop, on the owner's Windows machine from a clone on D:/: the owner talks
and reads this page; agents work in copies and land only verified work with a receipt; every
landing writes one line here; the record viewer opens from disk; Astra and Codex are reached
through the mailbox in the repository. Everything on this board is judged by whether it moves
that.

The owner's side is two things and nothing else: say it, read this page. The commands below are
for agents. The owner never types them; a session runs them when asked in words ("run the test",
"undo 7", "land 12", "what happened tonight").

For agents, on the D:/ clone (Git Bash, Python 3.11+, Node 22; Playwright optional):

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging.git /d/DiscStudio-staging
cd /d/DiscStudio-staging
python -m venv .venv && .venv/Scripts/python -m pip install -e "./pyto[drawing]"   # the scripts find .venv on their own
bash pyto/scripts/check_all.sh                                   # every suite, the same table as here
.venv/Scripts/python pyto/experiments/grouped-ablation/run_cached.py --out /d/pyto-hit --force   # one miss, then two hits, the second from a fresh process; overwrites its own scratch
node pyto/viewer/embed.mjs pyto/viewer/fixtures/pyto-grouped-ablation.json --out /d/pyto-hit/ticks.html   # open in a browser
```

For Astra or Codex, the owner reuses one sentence forever: "Pull the branch, read the newest
entries on pyto/questions.md, and continue." Every answer to an agent's question is written there,
in the owner's words and in the technical words side by side; the owner never carries the technical
half (owner, 2026-09-10: "Can't you translate between OSspeak and Samspeak").

## The frontier

What gets built next is planned as adds, not as a queue of tasks (owner, 2026-09-10: "we refine and
merge compatible things; each add includes an illustrative feature or is a few complementary things").
The adds, with what you will see when each lands, are on `pyto/FRONTIER.md`. A task opens from an add.

## Interrupts

The owner is interrupted for three things only: something they would want to know broke and
cannot be fixed without them; a decision that changes what gets built and has no safe default; a
milestone they asked for (the proof passed on their machine, a surface shipped). Everything else
is a line below, never a message. Defaults are taken and written in the owner's words; undo is a
sentence. An interrupt has one shape: what happened, in a plain sentence; what it means for the
owner, in one; what they can say, with the default named. No labels, receipts or paths. Knowing
it works is three lines, read in the morning: the proof line (green or red on D:/ in a fresh
clone), the product page, and the tally of landings and refusals with each reason. The owner did
not write this rule and can veto it in a sentence. A note addressed to the owner (a line starting
`**owner**`) must name which of the three it is as `[broke]`, `[decision]` or `[asked]`, and
`land.sh --note` refuses one that names none and writes nothing; everything else is a note, not an
interrupt.

## Today

One line per landing attempt, newest first, written by the landing script. Lines before 06:53 are
the day so far, in plain words.

- 2026-09-10 02:09 **landed** `task-37`: the frontier: pyto/FRONTIER.md holds every candidate on the record merged into nine adds, each one OS piece plus the feature that shows it, in the order that reads best; the board points at it; tasks open from adds (7 files since aec5160, suites green, receipt 20260910T020908Z-task-37)
- 2026-09-10 02:08 **started** `task-37`: the frontier: pyto/FRONTIER.md holds every candidate on the record merged into nine adds, each one OS piece plus the feature that shows it, in the order that reads best; the board points at it; tasks open from adds (copy EXP/37; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:52 **hand-off** from the cloud session, 2026-09-10: 46 landings since the loop was built; every decision is on pyto/questions.md in the owner's words; the Mac path is pyto/KT-MAC.md, six chunks for Codex, each ending with something to see; one known hazard for the Mac to debug (a task that edits land.sh can fail silently at commit; workaround in the file); nothing is running, no copies are open
- 2026-09-10 01:52 **landed** `task-36`: KT for the MacBook: pyto/KT-MAC.md walks Codex through six chunks that each end with something the owner sees (the board, receipts, a grade, the self-test, a landing), names the Mac landmines first, and records the cloud session's hand-off; board_page.py renders on Python 3.9 too (8 files since 90d3a93, suites green, receipt 20260910T015135Z-task-36)
- 2026-09-10 01:50 **started** `task-36`: KT for the MacBook: pyto/KT-MAC.md walks Codex through six chunks that each end with something the owner sees (the board, receipts, a grade, the self-test, a landing), names the Mac landmines first, and records the cloud session's hand-off; board_page.py renders on Python 3.9 too (copy EXP/36; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:50 **landed** `task-34`: interrupts are typed and a shared desk is graded by the class: land.sh --note refuses a line addressed to the owner (**owner**) unless it names one of the three reasons (broke, decision, asked), and neat land <id> --from <remote> <branch> --verify <cmd> --allow <paths> lets the landing repository's brief override the desk's packet (7 files since 3b8dd43, suites green, receipt 20260910T014936Z-task-34)
- 2026-09-10 01:46 **landed** `task-35`: students: grade.py check 4 matches each Tick as a list line of its own on the hand-off page, not as a substring anywhere, so deleting one step's line is caught even when the name appears elsewhere; the missing-Tick test removes Stats (9 files since 7f9752b, suites green, receipt 20260910T014535Z-task-35)
- 2026-09-10 01:38 **started** `task-35`: students: grade.py check 4 matches each Tick as a list line of its own on the hand-off page, not as a substring anywhere, so deleting one step's line is caught even when the name appears elsewhere; the missing-Tick test removes Stats (copy EXP/35; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:38 **started** `task-34`: interrupts are typed and a shared desk is graded by the class: land.sh --note refuses a line addressed to the owner (**owner**) unless it names one of the three reasons (broke, decision, asked), and neat land <id> --from <remote> <branch> --verify <cmd> --allow <paths> lets the landing repository's brief override the desk's packet (copy EXP/34; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:37 **landed** `task-33`: neat land from a remote: neat land <id> --from <url-or-remote> <branch> fetches a branch from another repository and lands it here with the same verifier, allowed paths and receipt, so a student's desk in its own repo can be shared into a class repo with one command; selftest covers it with a second scratch repository (6 files since 47210a7, suites green, receipt 20260910T013659Z-task-33)
- 2026-09-10 01:35 **landed** `task-32`: a score in the receipt: a verifier can print one line 'score: <passed> of <total>' and land.sh keeps it in the landing receipt and the Today line; neat list shows the score beside each landed task; verifiers that print no score are unchanged (8 files since 66e24ff, suites green, receipt 20260910T013426Z-task-32)
- 2026-09-10 01:27 **started** `task-33`: neat land from a remote: neat land <id> --from <url-or-remote> <branch> fetches a branch from another repository and lands it here with the same verifier, allowed paths and receipt, so a student's desk in its own repo can be shared into a class repo with one command; selftest covers it with a second scratch repository (copy EXP/33; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:27 **started** `task-32`: a score in the receipt: a verifier can print one line 'score: <passed> of <total>' and land.sh keeps it in the landing receipt and the Today line; neat list shows the score beside each landed task; verifiers that print no score are unchanged (copy EXP/32; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:27 **landed** `task-30`: every reader handles several produces: compare_local.py and pql_document.py in grouped-ablation stop assuming one into per invocation; tests for both (8 files since 887454c, suites green, receipt 20260910T012611Z-task-30)
- 2026-09-10 01:24 **landed** `task-29`: students: Mean and Median run in one Tick as parallel branches (the default under WhatIsATick), the hand-off says the honest reason (a receipt is per Calculation; a Tick is a step), evidence regenerated, and tick_laws shows the first Tick where work exceeds latency (15 files since be3fa2d, suites green, receipt 20260910T012337Z-task-29)
- 2026-09-10 01:19 **landed** `task-31`: board_page.py renders pyto/BOARD.md as one HTML page (the Today log as a timeline, open copies, lanes folded) with no dependencies, so the owner reads the board on a phone; the cloud session republishes it after every landing (7 files since 35172f8, suites green, receipt 20260910T011840Z-task-31)
- 2026-09-10 01:17 **started** `task-31`: board_page.py renders pyto/BOARD.md as one HTML page (the Today log as a timeline, open copies, lanes folded) with no dependencies, so the owner reads the board on a phone; the cloud session republishes it after every landing (copy EXP/31; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:15 **started** `task-30`: every reader handles several produces: compare_local.py and pql_document.py in grouped-ablation stop assuming one into per invocation; tests for both (copy EXP/30; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:14 **started** `task-29`: students: Mean and Median run in one Tick as parallel branches (the default under WhatIsATick), the hand-off says the honest reason (a receipt is per Calculation; a Tick is a step), evidence regenerated, and tick_laws shows the first Tick where work exceeds latency (copy EXP/29; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:09 **landed** `task-28`: neat pack refuses with a sentence when the packet has no Verify line instead of exiting silently; land.sh runs the verifier and the suite with the repository's venv first on PATH so a bare python3 in a Verify line means the same thing in a copy and on MAIN (8 files since f2954cc, suites green, receipt 20260910T010844Z-task-28)
- 2026-09-10 01:06 **started** `task-28`: neat pack refuses with a sentence when the packet has no Verify line instead of exiting silently; land.sh runs the verifier and the suite with the repository's venv first on PATH so a bare python3 in a Verify line means the same thing in a copy and on MAIN (copy EXP/28; it lands only on green, with a receipt, or is killed)
- 2026-09-10 01:06 **landed** `task-27`: a Calculation can produce several Parts: calc(... into=[a, b, ...]) publishes one Part per address from one invocation, the receipt lists every produce with its own digest, the record's produces and writes carry them all, and one-address calls are unchanged byte for byte (61 files since e2fbbd4, suites green, receipt 20260910T010544Z-task-27)
- 2026-09-10 01:05 **refused** `task-27`: verifier exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260910T010513Z-task-27/verifier.txt)
- 2026-09-10 01:04 **landed** `task-26`: Ticks as circuits: tick_laws.py checks any pyto-run-record@1 against the node law (inside a Tick no Calculation consumes a sibling's produce, no two siblings produce one Part) and the loop law (nothing consumes a Part produced later), and reports total work versus critical path per Tick; no kernel change (11 files since 71e2cbb, suites green, receipt 20260910T010331Z-task-26)
- 2026-09-10 00:38 **started** `task-27`: a Calculation can produce several Parts: calc(... into=[a, b, ...]) publishes one Part per address from one invocation, the receipt lists every produce with its own digest, the record's produces and writes carry them all, and one-address calls are unchanged byte for byte (copy EXP/27; it lands only on green, with a receipt, or is killed)
- 2026-09-10 00:32 **for Codex** `task-26`: the tick laws are Codex's to build, since its question set this off; brief on exp/26 at pyto/experiments/tasks/26/BRIEF.md; my builder was stopped and its work discarded
- 2026-09-10 00:27 **started** `task-26`: Ticks as circuits: tick_laws.py checks any pyto-run-record@1 against the node law (inside a Tick no Calculation consumes a sibling's produce, no two siblings produce one Part) and the loop law (nothing consumes a Part produced later), and reports total work versus critical path per Tick; no kernel change (copy EXP/26; it lands only on green, with a receipt, or is killed)
- 2026-09-10 00:16 **landed** `task-25`: the hand-off starts with a stopping rule: read the named files and no more, write the one question you would answer by reading another 100k tokens, ask the owner, stop; the answer goes on the root verbatim (8 files since b558911, suites green, receipt 20260910T001528Z-task-25)
- 2026-09-10 00:13 **started** `task-25`: the hand-off starts with a stopping rule: read the named files and no more, write the one question you would answer by reading another 100k tokens, ask the owner, stop; the answer goes on the root verbatim (copy EXP/25; it lands only on green, with a receipt, or is killed)
- 2026-09-09 23:23 **correction**: `task-3` (neat anywhere) was written by the owner's D:/ session under his own git identity, not by Codex; Codex never received it. The board and two replies said Codex. Earlier lines stand as written; this line is the record.
- 2026-09-09 23:22 **landed** `task-24`: the board says when a task starts, not only when it lands: neat new writes a started line, neat kill a killed line, and land.sh --note writes any one plain line, commits and pushes it (7 files since 9138dfc, suites green, receipt 20260909T232223Z-task-24)
- 2026-09-09 22:11 **landed** `task-23`: students: a homework-sized PCR with a hand-off page graded mechanically by grade.py, leaving only the plain-words explanation to a cold reader; no kernel change (13 files since d13fcd1, suites green, receipt 20260909T221055Z-task-23)
- 2026-09-09 22:10 **refused** `task-23`: check_all exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T221014Z-task-23/check_all.txt)
- 2026-09-09 22:05 **note**: research lane closed for now. Landed this stretch: task-9 (gate passed on second read), task-3 (neat anywhere), task-21 (studio run-record export), task-22 (receipts as Parts). Owner's framing, in his words: "Workspace. Educational." The workspace is the point; students are the audience it fits best. Queue from here is DiscStudio users first; no kernel tasks by default.
- 2026-09-09 21:56 **landed** `task-22`: Everything is a Part: with observe on, each invocation's receipt is also written into the store under the reserved px.receipt segment, so PQL can read receipts like anything else; with observe off nothing is written; no Calculation may bind a px.receipt address; the testimony stays byte-identical either way (207 files since 76bc3d2, suites green, receipt 20260909T215529Z-task-22)
- 2026-09-09 21:49 **landed** `task-21`: The studio exports its own run record: an Export run record action produces a pyto-run-record@1 JSON for the current composition through the existing adapter, and a link opens the Tick render page with that record embedded; no new state store, no renderer fork, no field whitelist (26 files since 0b502d0, suites green, receipt 20260909T214855Z-task-21)
- 2026-09-09 21:44 **landed** `task-3`: neat anywhere: the same seven commands in any git repo, no pyto assumptions, with a selftest that proves new, pack, land and undo in a scratch repo in under two minutes (18 files since e072078, suites green, receipt 20260909T214354Z-task-3)
- 2026-09-09 21:42 **refused** `task-21`: merge conflict with exp/21 in: pyto/viewer/embed.mjs scripts/browser_test.py src/review-data.js src/runtime.js tests/core.test.js 
- 2026-09-09 21:40 **landed** `task-9`: Add a fast, isolated check that land.sh's early refusal paths (bad package name, unknown branch, dirty file outside allowed paths) exit 1 and write a failed/*.json receipt without ever reaching check_all.sh, so the refusal contract is verified in under a second instead of only by hand-run scratch clones. (314 files since 1b38f28, suites green, receipt 20260909T213956Z-task-9)
- 2026-09-09 21:45 **note**: your D:/ session took ids 12 (proof.sh) and 13 (questions), so my two copies were renumbered: studio run-record export is now `task-21` (EXP/21, exp/21) and receipts as Parts is `task-22` (EXP/22, exp/22). Both builders had stalled; fresh ones are running. Codex delivered `task-3` (neat anywhere, selftest green); merging MAIN's `update` into it before landing.
- 2026-09-09 18:53 **landed** `task-20`: Hiding primitives: a SUBDUE-style miner over the paint studio's call graphs finds the helper sequences that recur across the sixteen families, scores them by compression, and reports them beside what the JavaScript port extracted by hand; workshop only, no images, no kernel change (26 files since a10b969, suites green, receipt 20260909T185240Z-task-20)
- 2026-09-09 18:19 **landed** `astra-discstudio-1`: Astra package one: the studio draws disc art through the ported painter and ships a printable shelf sheet; painted art inside the generic card (12 files since a10b969, suites green, receipt 20260909T181752Z-astra-discstudio-1)
- 2026-09-09 15:38 **landed** `task-19`: Painter port: the sixteen disc-art families and the two card renderers run in the browser as dependency-free JavaScript, byte-identical to the Python workshop across 432 family cases and 8 card cases (67 files since af0bf06, suites green, receipt 20260909T153806Z-task-19)
- 2026-09-09 15:37 **landed** `neat-ids-2`: task ids also count tasks landed on origin since the last pull (1 files since 9fba660, suites green, receipt 20260909T153644Z-neat-ids-2)
- 2026-09-09 15:35 **refused** `task-15`: merge conflict with exp/15 in: pyto/experiments/tasks/15/HANDOFF.md pyto/experiments/tasks/15/evidence/check_all.txt pyto/experiments/tasks/15/evidence/verify.txt pyto/experiments/tasks/15/packet.md 
- 2026-09-09 13:59 **landed** `task-18`: four worlds, one terminal: one page opens the ChainSpot, ChessLab, Wumpus, DiscStudio and pyto records side by side with a picker, the same tick page for every runtime, playback included (25 files since e1e888a, suites green, receipt 20260909T135832Z-task-18)
- 2026-09-09 13:51 **landed** `task-17`: cross-project hit: a second tiny domain reads the same per-user materials store and gets a verified hit on material the ablation experiment produced, with counters and a receipt (25 files since 12c6528, suites green, receipt 20260909T135010Z-task-17)
- 2026-09-09 13:41 **landed** `task-16`: watch it think: the tick page plays a record Tick by Tick with play, pause and step, each Calculation's reads, writes and value appearing when it finished, at recorded speed or slower (10 files since 12c6528, suites green, receipt 20260909T134004Z-task-16)
- 2026-09-09 09:58 **proof** green: fresh clone of c58032c, 6 steps, all green, receipt 20260909T095714Z-proof
- 2026-09-09 09:56 **landed** `task-15`: proof.sh gives each run its own output dir: the board's pyto-hit path is substituted like the clone path, so a second proof on one machine cannot trip over the first (6 files since 3b6c3ae, suites green, receipt 20260909T095540Z-task-15)
- 2026-09-09 09:48 **landed** `neat-reserve-id`: neat new pushes exp/<id> at once, so two clones can never pick the same task id (1 files since cf7ac33, suites green, receipt 20260909T094802Z-neat-reserve-id)
- 2026-09-09 09:56 The red proof was a leftover: step 5 refused to overwrite /d/pyto-hit from the previous proof. The suite and the viewer were green on D:/ in a fresh clone. The command now overwrites its own scratch; the next proof decides.
- 2026-09-09 09:51 **proof** red: fresh clone of 4875210, 6 steps, step 5 failed, receipt 20260909T094944Z-proof
- 2026-09-09 09:46 **landed** `task-12`: proof: the test as one script. proof.sh clones the branch fresh into a temp dir on this drive, runs the board's commands verbatim, writes one Today line with the result and a receipt under pyto/experiments/landings/proofs/ (16 files since 76bc3d2, suites green, receipt 20260909T094458Z-task-12)
- 2026-09-09 09:44 **landed** `task-14`: determinism log oracle survives a different interpreter: the log keeps naming its Python, the comparison normalizes the version and skips by name when the hash algorithm differs (5 files since 76bc3d2, suites green, receipt 20260909T094315Z-task-14)
- 2026-09-09 09:42 **refused** `task-14`: verifier exited 1 (see /d/pyto-socratic-20260909/pyto/experiments/landings/20260909T094234Z-task-14/verifier.txt)
- 2026-09-09 09:23 **landed** `task-11`: Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test (49 files since f2e0b8e, suites green, receipt 20260909T092312Z-task-11)
- 2026-09-09 09:23 **landed** `union-logs`: CHANGES.md, BOARD.md and questions.md merge by union: two writers appending never conflict (1 files since c2bd634, suites green, receipt 20260909T092226Z-union-logs)
- 2026-09-09 09:22 **refused** `task-11`: merge conflict with exp/11 in: pyto/CHANGES.md 
- 2026-09-09 09:10 **landed** `day3`: the render page, the materializer and the materials store, closed out by task 0; verified on the tree as it stands (257 files since 83422cf, suites green, receipt 20260909T091011Z-day3)
- 2026-09-09 09:10 **landed** `neat-update`: neat update brings MAIN into a copy; a packet's candidate is measured from the merge base, so MAIN's own commits never count as the task's change (2 files since 7d2448d, suites green, receipt 20260909T090927Z-neat-update)
- 2026-09-09 09:08 **landed** `task-0`: Day 3 close-out: the record contract says what both runtimes do (declared_consumes, nested array cap), run_cached derives hit or miss from counters, viewer and materializer agree on every fixture (24 files since f2e0b8e, suites green, receipt 20260909T090752Z-task-0)
- 2026-09-09 09:05 **refused** `task-0`: merge conflict with exp/0 in: pyto/experiments/grouped-ablation/evidence/run-6-cached/interpretation.md pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json 
- 2026-09-09 09:02 **landed** `task-2`: Address validator and census: parse any address into root, reserved second segment and rest; report every address in pyto that would fail the three-root rule; enforce nothing (145 files since 50ec3f7, suites green, receipt 20260909T090128Z-task-2)
- 2026-09-09 09:01 **landed** `suite-hygiene`: the experiment suite proves it changes nothing under pyto/src, instead of demanding a pristine tree that no branch landing can satisfy mid-merge (1 files since 67112e7, suites green, receipt 20260909T090043Z-suite-hygiene)
- 2026-09-09 08:59 **refused** `task-2`: check_all exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T085915Z-task-2/check_all.txt)
- 2026-09-09 08:52 **landed** `task-7`: Add a fast check that every bullet under BOARD.md's '## Today' starts with the exact '- YYYY-MM-DD HH:MM ' stamp the landing script's board() function writes, so a bug in that heredoc that corrupts the owner's one-page log is caught mechanically instead of by eyeballing. (121 files since 1b38f28, suites green, receipt 20260909T085216Z-task-7)
- 2026-09-09 08:52 **landed** `task-5`: Add a standalone, sub-second selftest that every committed landing receipt JSON (verified and failed) has the fields land.sh actually writes, so a schema regression in land.sh is caught without running check_all.sh or a scratch clone. (113 files since 1b38f28, suites green, receipt 20260909T085131Z-task-5)
- 2026-09-09 08:51 **landed** `task-4`: Stop `neat kill` from deleting the abandoned task's branch (local and on origin); only remove the disposable worktree directory. (105 files since 1b38f28, suites green, receipt 20260909T085038Z-task-4)
- 2026-09-09 08:50 **landed** `portable-sums`: floats add left to right (Python 3.11 and 3.13 agree bit for bit), every record regenerated, and the no-program-edits diff is taken against the program as last landed (45 files since 1c5447f, suites green, receipt 20260909T084944Z-portable-sums)
- 2026-09-09 08:48 **refused** `portable-sums`: check_all exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T084745Z-portable-sums/check_all.txt)
- 2026-09-09 08:47 **refused** `portable-sums`: check_all exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T084626Z-portable-sums/check_all.txt)
- 2026-09-09 08:46 **refused** `portable-sums`: check_all exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T084525Z-portable-sums/check_all.txt)
- 2026-09-09 08:45 **refused** `portable-sums`: check_all exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T084437Z-portable-sums/check_all.txt)
- 2026-09-09 08:41 **refused** `task-7`: the tree is not clean; a branch can only land into a clean tree (dirty: pyto/scripts/land.sh pyto/scripts/neat.sh )
- 2026-09-09 08:41 **refused** `task-5`: the tree is not clean; a branch can only land into a clean tree (dirty: pyto/scripts/land.sh pyto/scripts/neat.sh )
- 2026-09-09 08:41 **refused** `task-4`: the tree is not clean; a branch can only land into a clean tree (dirty: pyto/scripts/land.sh pyto/scripts/neat.sh )
- 2026-09-09 08:41 **refused** `landing-bookkeeping`: check_all exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T084119Z-landing-bookkeeping/check_all.txt)
- 2026-09-09 08:40 **refused** `task-7`: the tree is not clean; a branch can only land into a clean tree
- 2026-09-09 08:40 **refused** `task-5`: the tree is not clean; a branch can only land into a clean tree
- 2026-09-09 08:40 **refused** `task-4`: the tree is not clean; a branch can only land into a clean tree
- 2026-09-09 08:45 **refused** task 9 by the explicability gate: the hand-off's narrative claimed land.sh is exercised "two ways" and misplaced the BOARD.md reset, when check_land_refusals.sh actually makes three calls (no-args, unknown branch, dirty-outside-allow) with the reset sitting between the second and third; it stays packed (neat show 9)
- 2026-09-09 The Socratic session read the night's 92 commits and the docs at the tip (owner: "figure out what you're not getting"). What it was not getting: the test is the per-Tick page showing what each Calculation read and wrote with the value present, from both runtimes, not a suite run; the founding need is observability and the roadbumps were agent-context failures, which this session reproduced by repo-hunting; two agents talk to the owner at once, so "resolved" means resolved against the branch tip, where the explicability gate and `neat undo` already were; the owner's vocabulary (AHI, everything is a Part, fn and oc, checkpoint versus landed, green names a receipt) is the record's. Codex's unpushed Day 2 on D:/ holds evidence the branch lacks: two implementations of one brief cannot read each other's records, and digests drift between Python 3.11 and 3.14.
- 2026-09-09 Owner on the last open prompt: "I know nothing. U explain it. That's why this works." Renderers port to JS by default, site stays static. No open prompts left on the board; nine answers in the root tonight.
- 2026-09-09 Owner: "max telemetry"; the record keeps its commit and the stamp must name a landed commit. Owner: the past month of GitHub is the proof the process works. Seven answers in the root now.
- 2026-09-09 08:22 Fresh-clone proof on D:/ (owner: "I need proof im not one of them"): clone of 3b8b5e5, venv, install; one miss then one hit from a fresh process; the tick page rendered; the suite red on one test only: the record's `retained.commit` names a working-tree sha that no clone has. Lane 4's prompt, with evidence.
- 2026-09-09 08:21 **landed** `task-1`: AHI runs on the owner's Windows D:/: neat new works (host path for pip, python checks the install), the ablation fixture is bit-portable (no libm), the card server drains a 413 body, stripped child environments keep SystemDrive (65 files since 8604a0c, suites green, receipt 20260909T081928Z-task-1)
- 2026-09-09 08:16 **refused** `task-1`: MAIN is behind origin/HEAD by  commit(s) (someone landed elsewhere); run: git pull --rebase origin HEAD  then land again
- 2026-09-09 08:13 **landed** `windows-venv`: the scripts find the repository's .venv on their own, so isolated child processes import pyto on Windows too; the D:/ commands make that venv (4 files since 291b7f7, suites green, receipt 20260909T081311Z-windows-venv)
- 2026-09-09 11:40 Owner: what carries water immediately? The painter port (task 15, running): sixteen art families and two card renderers in the browser, byte-identical to the workshop across 440 cases, the verifier decides. It is Astra's package one too; whichever arrives, the same verifier scores it. Behind it, every DiscShelf and OnTheCourse format becomes shippable.
- 2026-09-09 11:20 Owner: "I want to know the things work but I shouldn't have to define an interrupt schema." The schema is now the system's own rule (section "Interrupts" above): three reasons to interrupt, one shape, three morning lines that say it works.
- 2026-09-09 11:05 Owner: is it making my life easier? Not yet: tonight added commands, prompts to paste and a relay. Rule from here: the commands are for agents; the owner says things and reads this page. "The test" is now one sentence to a session; Astra and Codex get one fixed sentence forever; the `{?}` root is read to the owner, never by the owner.
- 2026-09-09 10:20 Owner: go big, one more: a Fable uses Sonnets to self-improve in branching manners that must remain human explicable. Running now: Sonnets mine the record for small useful changes to the loop itself, each becomes a neat task in its own copy, and a cold reader who sees only the hand-off must explain it correctly before it may land (the explicability gate, now in LANDING.md). Losers stay packed.
- 2026-09-09 08:15 **refused** `task-1`: MAIN is behind origin/claude/python-ultracode-supercharge-st8hnu by 2 commit(s) (someone landed elsewhere); run: git pull --rebase origin claude/python-ultracode-supercharge-st8hnu  then land again
- 2026-09-09 10:05 Owner: a task Codex can run as a good neighbour, and a personal neat for the work laptop where only Rovo and Windsurf exist. Both are one task: 3, "neat anywhere", on `exp/3` with a brief sized for one agent (read five files, run one command, stop when the selftest passes). The prompt to paste is in `mailbox/to-gpt/0002`. When it lands, the two scripts copied into any repository give the work laptop the same seven commands, and an editor agent only has to run them.
- 2026-09-09 09:50 `neat undo` tested in the scratch clone: the probe task came back out of MAIN in 38 seconds with its own receipt and line. Two writers taught neat one thing: task ids now count the branches on origin too, so the D:/ session's task 1 and this session's next task cannot collide.
- 2026-09-09 09:35 Owner: minimal hard stops, go wild, but it has to augment me (AHI). Rule changed: everything that passes its verifier and the suite lands tonight, kernel changes included; each decision taken by default is written at the root in the owner's words; and `neat undo <id>` takes any landed task back out with a receipt, so the way back is one command, not git. This log is the owner's track; git is the machine's.
- 2026-09-09 09:20 Owner to bed. Tonight, in order, each as a neat task with a packet: land the Day 3 close-out (running); Day 3's own receipt; the studio exports its run record and opens the viewer (product, lands if its verifier and the browser check pass); a Mounts type ported from ChainSpot with the negative test (additive, lands if green); an address validator plus a census of what would fail the three-root rule, enforcing nothing (lands if green); a text `px ps` over a record, for a terminal without a browser (lands if green); receipts as Parts under `px.receipt.*` with the byte-identity test; an `oc` syscall-table prototype. Rule, as revised at 09:35: everything lands on green. Morning brief is this log plus `bash pyto/scripts/neat.sh list`.
- 2026-09-09 08:45 The loop closed both ways: the owner's Socratic session on D:/ pushed answers (Focus is DiscStudio; the brain dump is the conversation; addressing goes by default) and this session read them on its next push. Queue reordered: after Day 3 lands, DiscStudio surfaces come before the table and `px`. The D:/ session's fixes ride on `exp/1` and land through neat; landing now refuses when MAIN is behind origin, since two clones land into one branch.
- 2026-09-09 08:07 **refused** `task-1`: check_all exited 1 (see /d/pyto-socratic-20260909/pyto/experiments/landings/20260909T080631Z-task-1/check_all.txt)
- 2026-09-09 Socratic session on the owner's D:/: DiscStudio is the focus; the brain dump is the conversation, not a file; addressing goes by default (owner: "idk any of this"), a stress test found no Part root is enforced and Python has no mount type. On this Windows machine `neat new` failed (pip got a `/d/` path, the install check was a shell glob) and two suites fail: the ablation fixture uses `random.gauss`, whose libm calls drift one ULP from the Linux-made evidence, and the card server answers 413 without draining the body, which Windows turns into a connection abort. All three fixes are on `exp/1`, being verified there, to land through neat. "AHI runs on D:/" is not true here until they do.
- 2026-09-09 07:39 **landed** `landing-protocol`: one script, one receipt per landing, checkpoints labelled; neat as the caveman front (96 files since 4641ea8, suites green, receipt 20260909T073836Z-landing-protocol)
- 2026-09-09 07:38 **landed** `windows-safety`: digests ignore line endings, kernel LF, evidence regenerated, harness path from its own location, child processes keep SystemRoot on Windows (37 files since b2a2848, suites green, receipt 20260909T073723Z-windows-safety)
- 2026-09-09 07:34 **refused** `windows-safety`: the tree changed while the suites ran (someone is writing); nothing committed
- 2026-09-09 07:33 **refused** `windows-safety`: check_all exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T073247Z-windows-safety/check_all.txt)
- 2026-09-09 07:32 **refused** `windows-safety`: check_all exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T073146Z-windows-safety/check_all.txt)
- 2026-09-09 07:31 **refused** `windows-safety`: verifier exited 1 (see /home/user/DiscStudio-staging/pyto/experiments/landings/20260909T073102Z-windows-safety/verifier.txt)
- 2026-09-09 08:05 MAIN was red and I had said green: renormalizing the kernel's line endings changed the digests the experiment records carry for core.py and pcr.py, and my "green" came from a run before that change. Fix: digests ignore line endings everywhere, evidence for runs 1 to 4 regenerated, suite re-run before anything is claimed. The protocol now says a green claim names a receipt.
- 2026-09-09 07:40 Owner: landing I can control and understand, the context carried forward automatically to a fresh agent. neat built as seven commands over MAIN and EXP/<id>; packets travel inside the experiment; the hand-off page includes the clone steps and why pyto is worth an agent's time. End-to-end test running. Also: AHI runs on D:/ now, not later (LF attribute, digest fix, fresh-clone fixes).
- 2026-09-09 06:58 Branch mining done: 11 of 14 ChainSpot tips read, synthesis in `research/chainspot-branch-mining.md`; ChainSpot already decided worlds are mounts, not address segments. Round five below. Four tips being re-mined.
- 2026-09-09 06:53 The landing script now writes this log. Owner: the happy path must keep me in the loop.
- 2026-09-09 06:51 Owner: checks that cause friction get disabled. Protocol trimmed to one command on the happy path; special kernel rule dropped.
- 2026-09-09 06:48 Mailbox for Astra in the repository (`mailbox/to-gpt/0001`), since this session runs in the cloud and cannot see `D:\mailbox`. Writers get a copy of the whole tree (`git worktree`), no lock; the landing script compiles a copy back.
- 2026-09-09 06:47 **refused** `landing-protocol`: Day 3's workflow was still writing into `pyto/src`. The protocol caught the mixed-commit mistake on its first try.
- 2026-09-09 06:44 Landing protocol written: `LANDING.md`, `scripts/land.sh`, one receipt per landing.
- 2026-09-09 06:38 Astra answered: contract plus three bounded packages (painter port, studio record export, three formats), each with a verifier that exits 0 or 1.
- 2026-09-09 06:35 Painter port package: 432 family cases and 8 card cases with expected bytes, and the verifier.
- 2026-09-09 06:27 Owner: CV deferred; DiscShelf and OnTheCourse with many formats is the user demo.
- 2026-09-09 06:18 This board created. Earlier today: Days 1 and 2 landed (receipts, retain, fresh-process replay, second experiment with zero program edits); art tournament and registry (16 families, 8 renderers); observability ledger; the `{?}` root; Reframings 1 to 6.
- 2026-09-09 all day Day 3 running: the render page, the Python materializer, the materials store; in its second fix round.

## Lane 1: the kernel (this session owns it)

**Statement.** A portable AI kernel: PxC (five verbs: get, set, has, register, call) plus PCR and
Ticks as the sequencer, receipts as the trace, one JSON run record both runtimes read, and the PCR
render as the terminal. Namespaces are mount points; storage backends are chosen per mount by
that application's cold-start cost, measured, never configured; DuckDB (5.3 s) and OpenCV are out
of the runtime for that reason. JS is first class, Python is the workshop that replays, compares
and materializes the same records. Simple stays simple; extra effort earns its place. The demo
that justifies the week: `px add <address>`, verified in 2.5 seconds by replaying its own shipped
record in a fresh process. Verification is replay; there is no other kind. Scheduling, when it is needed: the JS event loop
is already the scheduler, and a Tick boundary is the yield point, the observation point and the
budget checkpoint at once; Calculations inside a Tick with no dependency between them may run on
workers with pixels transferred, the placement recorded in receipts so replay stays exact. The
first version is one `await` between Ticks; nothing more until a Tick is measured too slow. Two
kinds of Calculation and no third: `fn` is pure; `oc` (OperationalCalculation) is the syscall
table, the only place an effect happens (shell, file, git, network), and it records what it read
and what it produced as Parts so replay plays the Part back instead of re-running the effect.
Keep it simple and safe: an `oc` is allowed by name, never by pattern. Visibility is a flag, not a
build: `observe` costs nothing when off, the CV runtime runs with it off to hit the budget, and the
test that outputs are byte-identical with it on and off is the guarantee that stripping visibility
changes nothing else. Which is another reason for a somewhat compilable thing: the retained
program (the PQL document) plus the registry is the compile input, the workshop runs it with
visibility on and keeps the receipts, the compiled runtime runs the same document with visibility
off, and equal digests between the two are the proof the compile changed nothing. ChainSpot's
compiled-operation model (`planFingerprint`, `executeCompiledPlan` in the ChessLab contract
header) is that idea already; the record is what makes it checkable.

**Open prompt.** none. *Addressing, round five, taken by default.* The mining found ChainSpot already decided the hard
part: the world (a course, a game, a repo, a user's bag) is a mount outside the address, never a
segment, with a test that `px.DashsTrack.s1.badges` is never created. So `px.badges.px` means the
same thing in every world, and a cross-project hit is an identity check. Proposal: three roots
only, `px` (values), `fn` (pure), `oc` (effects), enforced for Parts the way `fn` already is;
second segment is the noun that outlives the stage that made it (`px.badges`, `px.shelf`,
`px.board`), which is where connection lives; four reserved second segments, `scratch`, `view`,
`proposal`, `run`; the mount id is content-derived (`imgid:<sha12>`, `disc:<bag>`,
`chess:<game>`) with human labels in a side map; `material` goes, because kind is a declared field
on the reference, not a prefix; `?` stays outside the address as the root of questions. Owner
(2026-09-09): "MDL is good but if u need to start with a wider footprint and refine over time
thats fine the whole point is learning while moving safely", and to the question itself, "idk
any of this". Taken as the default: this proposal is the target, a named wider footprint may ship
first, agents stress-test it (findings and seven agent defaults under `{?} AddressRootIsAMount`
in `questions.md`), and the owner is not asked about addressing again.

**Stands.** Days 1, 2 and 3 landed with receipts (receipts, retain, fresh-process replay, the
second experiment with zero program edits; the render page, the materializer, the materials
store, closed out by task 0). Landed tonight as well: digests and records that are the same bits
on Linux and Windows, the address validator and census (task 2). Running: the Mounts type (task
11). Day 4 (the table and `px`) waits behind the DiscStudio surfaces, per the owner's focus. Day 5 planned (node reads the table, a JS skill verified, cross-project hit,
SUBDUE and WebShaper on recorded graphs).

## Lane 2: DiscStudio surfaces (Codex, briefed from lane 1)

**Statement.** CV is deferred, on purpose: the demo that gets users is DiscShelf plus OnTheCourse,
with many formats supported easily because the pieces are right. A format is a Calculation over
the same Parts (a shelf, a bag, a round, a card), producing SVG, PNG, a printable sheet, a share
image, or a data export, through one fan-out PCR with receipts, so adding a format is adding one
Calculation and its record, never a new pipeline. The tournament's sixteen families and eight
renderers are the first formats. Users first; then CV lands on an audience. The surfaces, in
order: DiscShelf, OnTheCourse, formats (export and import), the PCR render inside the studio, the
reducer in both runtimes, competition Ticks with proposals written to `proposal.disc.*`, review
and comments on the (pcr, tick, invocation, part) anchor.

**Open prompt.** none. *Where do the Python renderers run for users?* Owner (2026-09-09): "idk what
you're saying. Idk any of this it just happened." Default taken: port to JS with digest equality,
the site stays static, Python is the workshop. The owner's contract, same night: "it needs to be
stable and explainable. I know nothing. U explain it. That's why this works."

**Stands.** The painter port landed (task 19): sixteen families and both card renderers run in
the browser, byte-identical to the workshop across 440 cases. Next in this lane: wire the port
into the studio's own art path under `AGENTS.md`, then the three formats (Astra's package three).
The studio's run-record export is being built in its own copy, landing only if `npm test`, the
viewer suite and the browser check pass.

## Lane 3: neat and tidy (the owner's neat expert)

**Statement.** neat is AI version control in one tree, caveman simple: one MAIN (the clone), one
EXP folder, a task is a number from 0. `neat new` makes EXP/<id>, a copy of MAIN with its own
python; `neat pack` writes the packet (intent, starting point, candidate, evidence, uncertain) and
the hand-off a fresh agent can explain from after cloning; `neat land <id>` merges into MAIN,
verifies there, writes the receipt and one line here, and EXP/<id> is gone; `neat drop` is "I like
two of the three files". Underneath, EXP/<id> is a git worktree on `exp/<id>`, deleted at landing,
so the tree the owner sees is one tree. A B+ tree can organize the records underneath later; it
does not provide isolation or landing by itself. neat keeps work-item and git state as Parts in
its own PxC so a change resolves against that memory deterministically; the computer manages git.
Declared intent stays separate from produced facts; proposals never write into facts. neat's own
semantics (persistent PxC, total-order telemetry, failed runs return a result) are the reference
for neat. The neat agent runs this board: ingest dumps and research, resolve which questions got
answered and which lanes moved, propose the next prompts. The brain dump is interactive: the owner talks, the Socratic session
writes the decision in the owner's words, commits and pushes; the owner opens no file and types
no git command.

**Open prompt.** none. The brief is at `research/briefs/neat-on-pxc-brief.md` with five `{?}`
entries for the expert to bring back.

**Stands.** neat has nine commands (new, pack, show, drop, land, undo, update, kill, list), tested
end to end in a scratch clone and used for every landing tonight; task 3 ("neat anywhere") is
briefed for Codex so the work laptop gets the same commands. Brief for the PxC-backed version
handed off; it should keep these commands. Ticket storage is a different mount from the board
render and is not budget-bound.

## Lane 4: the record and the room (observability)

**Statement.** The founding need is seeing what the algorithm used, per Tick. A Tick is the unit
at which you are allowed to look. The run record carries values as material (JSON, text, SVG
rendered as an image, PNG data URLs), and the render shows per Tick what each Calculation read,
wrote, took, and whether it was a hit. Agents annotate on the anchor (pcr, tick, invocation, part)
plus a grid coordinate for images, so notes carry meaning rather than being dumb receipts. The
`{?}` root is where an agent says "I was confused here"; the owner answers; the answer stays.

**Open prompt.** none. *Should a saved run remember its commit?* Owner (2026-09-09): "let's say max
telemetry since ur gonna try to selfbootstrap and go ham overnight lol". The field stays; a stamp
must name a landed commit, never a working-tree sha (the fresh-clone proof went red on exactly
that); the proof run after each landing is the check.

**Stands.** Observability ledger written; Day 3 landed the render and the materializer, and task 0
made the contract say what both runtimes do. Max telemetry per the owner: the record keeps its
commit, and a stamp names a landed commit.

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
