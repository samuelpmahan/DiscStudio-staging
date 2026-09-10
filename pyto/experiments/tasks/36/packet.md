# Task 36

Intent: KT for the MacBook: pyto/KT-MAC.md walks Codex through six chunks that each end with something the owner sees (the board, receipts, a grade, the self-test, a landing), names the Mac landmines first, and records the cloud session's hand-off; board_page.py renders on Python 3.9 too
Starting point: 90d3a93f3898ace1227415c9f93ebaae78a1d644 (land(task-34): interrupts are typed and a shared desk is graded by the class: land.sh --note refuses a line addressed to the owner (**owner**) unless it names one of the three reasons (broke, decision, asked), and neat land <id> --from <remote> <branch> --verify <cmd> --allow <paths> lets the landing repository's brief override the desk's packet)
Verify: python3 pyto/scripts/board_page.py pyto/BOARD.md > /tmp/kt-board.html && grep -q 'class="row' /tmp/kt-board.html && test -f pyto/KT-MAC.md && grep -q '^## Chunk 6' pyto/KT-MAC.md
Allow: pyto/KT-MAC.md pyto/scripts/board_page.py pyto/LANDING.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
