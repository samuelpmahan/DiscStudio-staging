# Task 34: interrupts are typed and a shared desk is graded by the class: land.sh --note refuses a line addressed to the owner (**owner**) unless it names one of the three reasons (broke, decision, asked), and neat land <id> --from <remote> <branch> --verify <cmd> --allow <paths> lets the landing repository's brief override the desk's packet

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
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/34
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/34:pyto/experiments/tasks/34/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 3b8dd43 origin/exp/34 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

interrupts are typed and a shared desk is graded by the class: land.sh --note refuses a line addressed to the owner (**owner**) unless it names one of the three reasons (broke, decision, asked), and neat land <id> --from <remote> <branch> --verify <cmd> --allow <paths> lets the landing repository's brief override the desk's packet

## Starting point

e99ce55ac146f7373dc8d42bcb607769c872d614 (land(task-33): neat land from a remote: neat land <id> --from <url-or-remote> <branch> fetches a branch from another repository and lands it here with the same verifier, allowed paths and receipt, so a student's desk in its own repo can be shared into a class repo with one command; selftest covers it with a second scratch repository). MAIN may have moved since: `git log --oneline 3b8dd43..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/BOARD.md
- M  pyto/LANDING.md
- M  pyto/scripts/land.sh
- M  pyto/scripts/neat.sh

```
pyto/BOARD.md        |  5 ++++-
 pyto/LANDING.md      | 11 +++++++---
 pyto/scripts/land.sh | 11 ++++++++++
 pyto/scripts/neat.sh | 57 +++++++++++++++++++++++++++++++++++++++++++++-------
 4 files changed, 73 insertions(+), 11 deletions(-)
```

## Evidence

- verify: `bash pyto/scripts/neat.sh selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         193  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    248  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             14  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} InterruptTagAnywhere: the reason tag may sit anywhere in the line (`**owner** the suite is red [broke]` passes as readily as `**owner** [broke] the suite is red`), and matching is literal and case sensitive, so `[Broke]` or `(broke)` is refused. Tightening it to "the tag comes first, right after `**owner**`" would make every interrupt read the same way at the price of refusing lines that name their reason plainly in the middle. Nothing checks that the tag is the truth: the rule makes the writer choose one of the three, it does not judge the choice.
{?} InterruptOnlyOwnerLines: only a line beginning `**owner**` is checked. A **started**, **killed**, **landed**, **refused** or **for Codex** line, or any plain note, is untouched even when it is addressed to the owner in words, and a line that mentions `**owner**` after the first character is not an interrupt. That is the board's own wording ("everything else is a note, not an interrupt") read literally; say the word if a note should be checked wherever it addresses the owner.
{?} NeatLandOverrideScope: `--verify`/`--allow` are accepted only after `--from`, so a local `neat land <id>` still runs exactly the packet its own copy packed and there is no way to grade your own desk with a different command from the command line. This answers task 33's `{?} NeatFromVerify` in the direction it named (the class's tests are the real grade) without opening the same door for ordinary landings.
{?} GradedHereMeansOverridden: the Today line says `graded here` whenever either flag is given, including `--allow` alone, where the verifier is still the desk's and only the scope changed. One marker for "this landing was judged by the landing repository's brief, not the packet's" seemed better than two; the receipt is the place that says exactly which command ran and which paths were allowed.
{?} PacketKeepsTheDeskWords: an override changes only what this landing runs; the packet that lands at `pyto/experiments/tasks/<id>/` still carries the desk's own Verify and Allow lines, so the record shows both what the student claimed and what the class checked (the receipt). Rewriting the landed packet to the grader's brief would lose the student's half of that.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 34 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 34`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-34): interrupts are typed and a shared desk is graded by the class: land.sh --note refuses a line addressed to the owner (**owner**) unless it names one of the three reasons (broke, decision, asked), and neat land <id> --from <remote> <branch> --verify <cmd> --allow <paths> lets the landing repository's brief override the desk's packet`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
