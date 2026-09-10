# Task 56

Intent: the frontier says what the second wave landed: FRONTIER.md's Landed adds gains one line each for tasks 48 (the JS runtime speaks the same schedule), 49 (oc, effects with receipts), 50 (effects on the page), 51 (CI runs to completion), 52 (USE.md, executed) and 55 (green on macOS and Windows), each named by the task's own intent line, so the one file that says what got built is complete at the end of the sprint
Starting point: 55471cac439324a523e200ee3520136ce32d64e6 (land(task-55): green on macOS and Windows: the three failures at a9e3b1a were the tests, not the kernel. test_use.py compares CRLF stdout on Windows to LF text; test_classroom.py spells bash so Windows resolves WSL's instead of Git's; test_parallel's overlap check gave four threads 50 ms to start and a slow macOS runner took 114. Each test is made true on the platform it runs on without loosening what it proves)
Verify: grep -q 'task 48' pyto/FRONTIER.md && grep -q 'task 49' pyto/FRONTIER.md && grep -q 'task 50' pyto/FRONTIER.md && grep -q 'task 51' pyto/FRONTIER.md && grep -q 'task 52' pyto/FRONTIER.md && grep -q 'task 55' pyto/FRONTIER.md
Allow: pyto/FRONTIER.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
