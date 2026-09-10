"""neat: the owner's work-item namespace. Today, the question loop (`review`).

`{?} Label: description` is the mark an agent leaves under a packet's
"## Uncertain" when it is unsure; `pyto/questions.md` is the same mark's root.
`pyto.neat.review` turns the scattered `{?}` marks into one small, deterministic
batch the owner answers a number at a time (`{?} TinyQuestions`,
`pyto/questions.md`): `neat ask` collates them, `neat answer` captures, freezes
and files one reply, `neat answers` lists what has been filed. See
`pyto/scripts/neat.sh` and `pyto/tests/test_neat_review.py`.

Deliberately no re-export here: `import pyto.neat.review` (as `walk.py` and the
tests do) is the one way in, so `python -m pyto.neat.review` -- the CLI `neat
ask`/`neat answer`/`neat answers` shell out to -- does not also find its own
module pre-loaded under a second name.

`pyto.neat.diff` (task 66) computes a candidate pair's difference before it is
shown; `pyto.neat.gate` (task 67) is the join's gate: only a human's approval of an
exact head sha opens a landing.
"""
