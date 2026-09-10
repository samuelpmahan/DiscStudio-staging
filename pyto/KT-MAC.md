# KT: the workshop on the MacBook, one chunk at a time

For the owner, with Codex doing the typing. Each chunk ends with something you can see. Do them
in order; stop after each one. The machine is an old MacBook Air, so nothing heavy runs until
chunk 5, and chunk 5 is optional.

The sentence you paste to Codex for every chunk, changing only the number:

```
Read pyto/KT-MAC.md in the clone (or on the branch claude/python-ultracode-supercharge-st8hnu of
samuelpmahan/DiscStudio-staging), do chunk N only, exactly as written, stop when I can see what
the chunk says I will see, and tell me what you saw in one line. Fix nothing outside the chunk;
if something fails, show me the last ten lines and stop.
```

Mac landmines, known in advance (Codex reads these first):

- macOS ships bash 3.2. `neat.sh`, `land.sh` and `check_all.sh` run on it. `proof.sh` does not
  (it uses `mapfile`); it needs `brew install bash` and `/opt/homebrew/bin/bash pyto/scripts/proof.sh`
  or `/usr/local/bin/bash` on an Intel Air. Nothing before chunk 6 needs proof.sh.
- The system `python3` on an older macOS is 3.9. The kernel needs 3.10 or newer: `brew install
  python@3.12`, then use `python3.12` explicitly to make the venv. After that the scripts find the
  venv on their own.
- Node 22 is only for the Tick viewer (a static HTML page) and the viewer test suite. Without it,
  chunks 1 to 4 still work; the viewer html is skipped with a printed note.
- No Playwright, no Chromium, no browser tests on this machine. They are not in any chunk.
- BSD `sed` and `date` are fine: the scripts avoid GNU-only flags. If Codex ever reaches for
  `sed -i`, it needs `sed -i ''` on a Mac; it should not need to.

## Chunk 0: tools (10 minutes, once)

Codex checks and installs, nothing else: `git --version` (Xcode command line tools if missing:
`xcode-select --install`), Homebrew, `brew install python@3.12`, and optionally `brew install
node@22` and `brew install bash`. Then `git config --global user.name` and `user.email` set to
anything (landings commit under them).

You see: three version lines printed: git, python3.12, and node or "no node".

## Chunk 1: the board (5 minutes, no dependencies)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging.git ~/DiscStudio-staging
cd ~/DiscStudio-staging
python3.12 pyto/scripts/board_page.py pyto/BOARD.md > ~/board.html && open ~/board.html
```

You see: the board in Safari, the same page the cloud session rendered: the counts strip, The
test, the Today timeline. That is the one page. No venv, no install, nothing downloaded but the
clone (about 100 MB with history).

## Chunk 2: a program leaves receipts (10 minutes)

```
cd ~/DiscStudio-staging
python3.12 -m venv .venv && .venv/bin/pip install -e "./pyto[drawing]"    # Pillow is the only dependency
source .venv/bin/activate
cd pyto/experiments/students
python homework.py --out /tmp/hw
python grade.py --run /tmp/hw --handoff HANDOFF.md
open /tmp/hw/tick-viewer.html        # only if node is installed; otherwise skip this line
```

You see: the class-scores homework run (four steps, the middle one two Calculations side by
side), then the grader's report: four mechanical checks PASS, a "for the cold reader" block, and
the caveat line. If node is there, the Tick viewer opens: one section per step, what each
Calculation read and wrote. Files: `/tmp/hw/record.json` is the run record, `receipts.json` the
receipts. This is "show your work" on your own machine.

## Chunk 3: the Jira (3 minutes)

```
cd ~/DiscStudio-staging
bash pyto/scripts/neat.sh list | head -20
bash pyto/scripts/questions.sh | head -30
ls pyto/experiments/landings | tail -5
cat "pyto/experiments/landings/$(ls pyto/experiments/landings | grep task- | tail -1)/receipt.json"
```

You see: every task with its state and score column; the open questions with their defaults; the
last landing receipts by name; one receipt in full (package, base, result, verifier, suite,
claimed files). Nothing here is a claim without one of these.

## Chunk 4: neat proves itself here (3 minutes)

```
cd ~/DiscStudio-staging
bash pyto/scripts/neat.sh selftest
```

You see: twelve `selftest ...: pass` lines. It built a throwaway repository under /tmp, ran new,
pack, land, undo, a scored landing, a landing from a second repository ("a shared desk"), and
the interrupt rule, then deleted it. Two git lines about "push negotiation" are noise.

## Chunk 5 (optional, the heavy one): every suite (10 to 20 minutes on an old Air)

```
cd ~/DiscStudio-staging
source .venv/bin/activate
bash pyto/scripts/check_all.sh
```

You see: the per-suite table and `ALL SUITES PASSED`. Without node the viewer rows fail by
name and the last line says SOME SUITES FAILED; that is expected on a machine without node, and
every Python row is still green. Skip this chunk if the machine is struggling; nothing after it
needs it.

## Chunk 6: your first landing on this machine (10 minutes)

```
cd ~/DiscStudio-staging
source .venv/bin/activate
bash pyto/scripts/neat.sh new "mac: a note in KT-MAC.md saying which macOS and python this ran on" --verify "grep -q 'ran on' pyto/KT-MAC.md" --allow "pyto/KT-MAC.md pyto/experiments/tasks"
```

Codex then appends one line to `EXP/<id>/pyto/KT-MAC.md` under "## Ran on" (below): the macOS
version, the python version, node or not, and the date. Then:

```
bash pyto/scripts/neat.sh pack <id>
bash pyto/scripts/neat.sh land <id>
python3.12 pyto/scripts/board_page.py pyto/BOARD.md > ~/board.html && open ~/board.html
```

You see: the board again, with a **started** line and a **landed** line for your task at the
top of Today, written by the scripts on your machine, and the receipt under
`pyto/experiments/landings/`. That is AHI running on the MacBook: you said it, an agent worked in
a copy, the landing verified it, the board says so.

## Ran on

(one line per machine, appended by chunk 6)

## What the next session should know (the cloud session's hand-off)

- A task that changes `land.sh` itself can fail silently at the commit step: the landing merges the
  candidate onto MAIN before verifying, so bash is executing a file that changed under it. Task 34
  hit this. Workaround used: run the landing from the script text read into memory
  (`bash -c "$(cat pyto/scripts/land.sh)" pyto/scripts/land.sh task-N --from exp/N ...`). The real fix is
  for land.sh to copy itself to a temp file and re-exec before merging; it is not done yet.
- Landings run the verifier with the repository's `.venv` first on PATH (task 28); before that a
  bare `python3` in a Verify line failed on MAIN and passed in the copy.
- Two landings cannot share MAIN at once; land one, then the next. `neat update <id>` brings MAIN
  into a copy before its landing when MAIN moved.
- Codex rewrote a packet's header once (task 26). The header above "## Uncertain" is neat's; an
  agent writes only under Uncertain. Task 28 made a missing Verify line refuse loudly.
- Task ids collided three times when two clones counted from zero; ids now count origin's
  `exp/*` branches too. If a collision still happens, rename the branch and the tasks folder
  before landing.
- Everything the owner decided is on `pyto/questions.md` in his words with the default taken.
  The newest entries (StoppingRule, WhatIsATick, TicksAsCircuits, ResultReadsAreReads,
  NeatLearning, DeterministicInterrupts) are the current design conversation.
- The board page: `python3 pyto/scripts/board_page.py pyto/BOARD.md > board.html`. The cloud
  session published it at a claude.ai artifact link; on the Mac it is the same file, opened locally.
- The one sentence for any agent: "Pull the branch, read the newest entries on
  pyto/questions.md, and continue." Answers to agent questions go there, plain and technical
  side by side. The owner never carries the technical half.
