# Task 67

Intent: the join asks once, and only a human can open it: pyto/src/pyto/neat/gate.py registers fn.neat.gate.evaluate (a landing's subject digest from its receipt, a frozen human event in, neat.blok.gate.<reviewDigest> out; approve of the exact sha opens, revise, reject and retain keep it closed, empty text, a stale sha, a missing event and an agent-written event stay closed) and oc.neat.gate.githubReview (the approving reviews on a pull request head sha by login, read with GITHUB_TOKEN); land.sh calls neat gate before the commit when .neat/gate names github and refuses by name otherwise; the receipt records the gate; the walk shows approved-by or unapproved per step
Starting point: be49dffc799092b2fb9fd9731509a883f637b382 (board: **started** `task-66`: the difference is computed before it is shown, an)
Verify: cd pyto && python -m unittest tests.test_neat_gate && bash scripts/neat.sh selftest
Allow: pyto/src/pyto/neat/gate.py pyto/src/pyto/neat/__init__.py pyto/tests/test_neat_gate.py pyto/scripts/neat.sh pyto/scripts/land.sh pyto/scripts/walk.py pyto/tests/test_walk.py pyto/KT-MAC.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} SecretsAreNotEffects: Effects.env records the value it reads, so the GitHub token is read with os.environ and never through the handle; a secret is an effect the ledger must not carry, and the handle has no verb for that.
{?} HttpIsNotAnEffectKind: the GitHub requests are not ledgered (the handle has write_text, read_text, now_ms, random, env); the event they return is the Part, the request is not; a network verb on the handle is a kernel decision.
{?} NeatIsAMount: the gate Part is spelled neat.blok.gate.<digest> as the owner's local YAML spells it, while address.py reads neat as a mount outside the address (questions.md 119, 410); address.py enforces nothing, so both spellings run; one has to win.
{?} SubjectIsTheHeadSha: the frozen subject is the package plus the candidate's head sha, because the sha fixes the packet and every claimed byte; the receipt's per-file digests are derived from it and are not in the subject.
{?} StubOpensTheSelftest: a stub event can open a landing in the selftest so the host path is exercised; its receipt says trusted false and stub_allowed true and the walk says stub gate, never trusted; whether a stub should be able to open anything at all is the owner's.
