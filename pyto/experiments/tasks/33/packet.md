# Task 33

Intent: neat land from a remote: neat land <id> --from <url-or-remote> <branch> fetches a branch from another repository and lands it here with the same verifier, allowed paths and receipt, so a student's desk in its own repo can be shared into a class repo with one command; selftest covers it with a second scratch repository
Starting point: d8ccde810b9fc2f600c27795c8247c2fb956f7a1 (board: **started** `task-32`: a score in the receipt: a verifier can print one)
Verify: bash pyto/scripts/neat.sh selftest
Allow: pyto/scripts/neat.sh pyto/scripts/land.sh pyto/LANDING.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} NeatFromRefName: the fetched desk lands from `refs/neat/from/<id>`, namespaced by id so it never collides with a local `exp/<id>` (task 0 here and task 0 on a desk are different tasks), and deleted on success and on refusal; a plain branch `neat-from-<id>` would be visible in `git branch` instead, at the price of showing up in every branch listing. Say the word if you want it visible.
{?} NeatFromVerify: "the same verifier" is read literally: the shared packet's Verify line is run in the class repo exactly as written. If the desk's Verify names a path only that desk has (its own test file), the verifier exits non-zero and the landing refuses with that exit code and a failed receipt, which is honest but unhelpful for a class where the teacher's tests are the real verifier. The alternative is a `--verify` override on the landing that replaces the packet's line; that means a shared desk can be graded by the class's verifier rather than its own.
{?} NeatFromId: the id on the command line names the packet path inside the incoming branch (`<tasks>/<id>/packet.md`), so a desk packed as task 3 must land here as task 3 and takes that number in the class repo. Ids are not translated. If two desks pack task 0, the second one lands only after the first has landed or been undone.
{?} NeatFromCleanup: a landing from a remote deletes nothing on the other side and nothing local: no `rm -rf EXP/<id>` (that folder here would be a different task) and no `push origin --delete exp/<id>`. The desk's branch stays until its owner removes it; unsharing here is `neat undo <id>`.
