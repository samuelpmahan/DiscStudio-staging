# Task 31

Intent: board_page.py renders pyto/BOARD.md as one HTML page (the Today log as a timeline, open copies, lanes folded) with no dependencies, so the owner reads the board on a phone; the cloud session republishes it after every landing
Starting point: 35172f8a59efd610d94dcee724aaea39bdf809c0 (board: **started** `task-30`: every reader handles several produces: compare_lo)
Verify: python3 pyto/scripts/board_page.py pyto/BOARD.md > /tmp/board-check.html && python3 -c "import re,sys;s=open('/tmp/board-check.html').read();bad=[t for t in ['section','details','ul','li','p','pre'] if len(re.findall('<'+t+'[ >]',s))!=len(re.findall('</'+t+'>',s))];sys.exit(1 if bad or 'class=\"row' not in s else 0)"
Allow: pyto/scripts/board_page.py pyto/LANDING.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
