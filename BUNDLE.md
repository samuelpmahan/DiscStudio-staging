# neat-pyto-ds-bundle

One zip, the whole workshop: neat (AI version control in one tree), pyto (the kernel, its
experiments and receipts), and DiscStudio (the site that uses them). Built by GitHub Actions on
every push to main.

## Grab it (agent or human)

```
curl -L -o bundle.zip https://github.com/samuelpmahan/neat-pyto-ds-bundle/releases/latest/download/neat-pyto-ds-bundle.zip
unzip -q bundle.zip && cd neat-pyto-ds-bundle
cat BUNDLE-COMMIT.txt        # which commit this is
```

Or clone: `git clone https://github.com/samuelpmahan/neat-pyto-ds-bundle`.

## Then

- `pyto/BOARD.md` is the one page: what the test is, what landed today, what is open.
- `pyto/questions.md` is the root: every open question with its default.
- `pyto/LANDING.md` is how anything gets in, and the neat commands.
- `bash pyto/scripts/proof.sh` runs the whole loop from a fresh clone and writes its receipt.
- `bash pyto/scripts/neat.sh selftest` proves neat in a scratch repo in under two minutes.
- `bash pyto/scripts/neat.sh new "what you want"` starts a task; `pack`, `land`, `undo` do the rest.

Python 3.11+ and Node 22. `python -m venv .venv && .venv/bin/pip install -e "./pyto[drawing]"` first.
