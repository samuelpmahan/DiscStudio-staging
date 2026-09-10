"""The question loop (`pyto.neat.review`): collate is deterministic and omits what
is answered, capture refuses a blank reply, freeze is a one-way digest that
tolerates only the bytes it already has, file appends verbatim and marks the
label answered, every run leaves a `pyto-run-record@1` document a second reader
validates, and `neat ask`/`neat answer`/`neat answers` round-trip through the
real shell script. Every test that writes uses a tempfile tree; none ever
touches the real `pyto/questions.md`."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PYTO = os.path.dirname(HERE)

import pyto.neat.review as review  # noqa: E402  (editable install: pyto/src is already on sys.path)

# The second reader of the shared run-record format (tests/test_materialize.py does the same).
VIEWER_TEST_DIR = os.path.join(PYTO, "viewer", "test")
if VIEWER_TEST_DIR not in sys.path:
    sys.path.insert(0, VIEWER_TEST_DIR)
from record_schema import validate as validate_record  # noqa: E402

CALCULATION_ADDRESSES = {
    "fn.neat.review.collate", "oc.neat.review.captureHumanText",
    "fn.tidy.freezeText", "fn.neat.review.file",
}


def _write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _scratch_root() -> tuple[str, str]:
    """(tmp dir to clean up, the `pyto/` root inside it)."""
    tmp = tempfile.mkdtemp(prefix="neat-review-")
    return tmp, os.path.join(tmp, "pyto")


def _one_packet(root: str, task_id: str, *questions: str) -> None:
    lines = "\n".join(questions)
    _write(os.path.join(root, "experiments", "tasks", task_id, "packet.md"),
           f"Intent: task {task_id}\n\n## Uncertain\n\n{lines}\n")


def _bootstrap_scratch_repo(tmp: str) -> str:
    """A minimal git repo shaped like this one -- `pyto/pyproject.toml`, a real copy of
    `neat.sh`, one packet with one open question -- with an origin remote, built the
    same way `cmd_selftest` builds its own (`scripts/neat.sh` lines ~460-475): a bare
    origin, a working clone, one commit, one push, so nothing in the script's
    unconditional startup (`git rev-parse --abbrev-ref HEAD`, `git remote get-url
    origin`) has nothing to read."""
    origin = os.path.join(tmp, "origin.git")
    work = os.path.join(tmp, "work")
    subprocess.run(["git", "init", "-q", "--bare", origin], check=True)
    subprocess.run(["git", "init", "-q", work], check=True)
    subprocess.run(["git", "-C", work, "config", "user.email", "neat-review-test@example.invalid"], check=True)
    subprocess.run(["git", "-C", work, "config", "user.name", "neat-review-test"], check=True)

    pyto_dir = os.path.join(work, "pyto")
    os.makedirs(os.path.join(pyto_dir, "scripts"))
    _write(os.path.join(pyto_dir, "pyproject.toml"), '[project]\nname = "scratch"\nversion = "0"\n')
    real_neat_sh = os.path.join(PYTO, "scripts", "neat.sh")
    copy_path = os.path.join(pyto_dir, "scripts", "neat.sh")
    shutil.copy(real_neat_sh, copy_path)
    os.chmod(copy_path, 0o755)
    _one_packet(pyto_dir, "1", "{?} Alpha: first question")

    subprocess.run(["git", "-C", work, "add", "-A"], check=True)
    subprocess.run(["git", "-C", work, "commit", "-q", "-m", "init"], check=True)
    subprocess.run(["git", "-C", work, "remote", "add", "origin", origin], check=True)
    subprocess.run(["git", "-C", work, "push", "-q", "-u", "origin", "HEAD"], check=True)
    return work


class Collate(unittest.TestCase):
    """(a) twice over the same tree is the same bytes."""

    def test_same_tree_same_bytes(self):
        tmp, root = _scratch_root()
        try:
            _one_packet(root, "1", "{?} Alpha: a question", "{?} Beta: another")
            first = review.collate({"pyto_root": root, "n": 3})
            second = review.collate({"pyto_root": root, "n": 3})
            self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
            self.assertEqual(review.digest_value(first), review.digest_value(second))
        finally:
            shutil.rmtree(tmp)

    def test_answered_label_is_omitted_and_numbering_stays_stable(self):
        """(b) two packets, one answer: the answered label is gone, the rest renumber."""
        tmp, root = _scratch_root()
        try:
            _one_packet(root, "1", "{?} Alpha: first", "{?} Beta: second")
            _one_packet(root, "2", "{?} Gamma: third")
            review.write_part(
                os.path.join(root, "experiments", "review", "answers", "Beta.json"),
                "neat.review.answer.Beta", {"label": "Beta", "n": 0, "k": 0, "sha256": "0" * 64},
            )
            batch = review.collate({"pyto_root": root, "n": 1})
            rows = [(item["number"], item["label"], item["task"], item["origin"]) for item in batch["items"]]
            self.assertEqual(rows, [
                (1, "Alpha", "task-1", "packet"),
                (2, "Gamma", "task-2", "packet"),
            ])
        finally:
            shutil.rmtree(tmp)

    def test_root_and_diff_origins_carry_their_own_task_field(self):
        tmp, root = _scratch_root()
        try:
            _write(os.path.join(root, "questions.md"),
                   "# {?} The root\n\n### {?} Zeta\nIs this the first one?\nStatus: open.\n")
            review.write_part(
                os.path.join(root, "experiments", "review", "diffs", "sample.json"),
                "tidy.diff.sample", {"remainder": [{"label": "Eta", "text": "left over"}]},
            )
            batch = review.collate({"pyto_root": root, "n": 1})
            by_label = {item["label"]: item for item in batch["items"]}
            self.assertEqual(by_label["Zeta"]["task"], "root")
            self.assertEqual(by_label["Zeta"]["origin"], "root")
            self.assertEqual(by_label["Zeta"]["text"], "Is this the first one?")
            self.assertEqual(by_label["Eta"]["task"], "diff")
            self.assertEqual(by_label["Eta"]["origin"], "diff")
            self.assertEqual(by_label["Eta"]["text"], "left over")
        finally:
            shutil.rmtree(tmp)


class Capture(unittest.TestCase):
    """(c) captureHumanText refuses "" and "   "."""

    def test_refuses_empty_and_whitespace(self):
        for text in ("", "   ", "\t\n"):
            with self.assertRaisesRegex(ValueError, "Alpha.*empty text|empty text.*Alpha"):
                review.capture_human_text({"n": 1, "k": 2, "label": "Alpha", "text": text})


class Freeze(unittest.TestCase):
    """(d) freezeText tolerates the same bytes, refuses a different rewrite."""

    def test_identical_rewrite_tolerated_different_refused(self):
        capture = {"n": 1, "k": 1, "label": "Alpha", "text": "hello"}
        first = review.freeze_text({"capture": capture})
        self.assertEqual(first["bytes"], "hello")
        again = review.freeze_text({"capture": capture, "existing": first})
        self.assertEqual(first, again)
        with self.assertRaisesRegex(ValueError, "already frozen"):
            review.freeze_text({"capture": {**capture, "text": "world"}, "existing": first})


class FileAnswer(unittest.TestCase):
    """(e) file appends the bytes verbatim (quotes, a non-ASCII character) and creates the answer file."""

    def test_appends_verbatim_and_creates_answer_file(self):
        tmp, root = _scratch_root()
        try:
            reply = 'yes — "exactly" that, café'
            _one_packet(root, "1", "{?} Alpha: a question")
            review.run_ask(root)
            part = review.run_answer(root, 1, 1, reply, technical="a technical gloss")

            with open(os.path.join(root, "questions.md"), encoding="utf-8") as handle:
                questions = handle.read()
            self.assertIn(f'"{reply}"', questions)
            self.assertIn("Technical: a technical gloss", questions)
            self.assertIn("Filed from batch 1 item 1, frozen ", questions)

            answer_path = os.path.join(root, "experiments", "review", "answers", "Alpha.json")
            self.assertTrue(os.path.isfile(answer_path))
            with open(answer_path, encoding="utf-8") as handle:
                on_disk = json.load(handle)
            self.assertEqual(on_disk, part)
            self.assertEqual(on_disk["address"], "neat.review.answer.Alpha")
            self.assertEqual(on_disk["value"]["label"], "Alpha")
            self.assertEqual(on_disk["sha256"], review.digest_value(on_disk["value"]))
        finally:
            shutil.rmtree(tmp)


class RunRecords(unittest.TestCase):
    """(f) every run record validates and names its Calculations by address."""

    def test_ask_and_answer_leave_valid_run_records(self):
        tmp, root = _scratch_root()
        try:
            _one_packet(root, "1", "{?} Alpha: a question")
            review.run_ask(root)
            review.run_answer(root, 1, 1, "yes")

            runs_dir = os.path.join(root, "experiments", "review", "runs")
            with open(os.path.join(runs_dir, "ask-1.json"), encoding="utf-8") as handle:
                ask_record = json.load(handle)
            with open(os.path.join(runs_dir, "answer-1-1.json"), encoding="utf-8") as handle:
                answer_record = json.load(handle)

            validate_record(ask_record)
            validate_record(answer_record)

            seen = {
                invocation["calculation"]["address"]
                for record in (ask_record, answer_record)
                for tick in record["ticks"]
                for invocation in tick["invocations"]
            }
            self.assertEqual(seen, CALCULATION_ADDRESSES)
        finally:
            shutil.rmtree(tmp)


class BashRoundTrip(unittest.TestCase):
    """(g) `neat ask` and `neat answer` through the real `neat.sh`, in a scratch copy of the tree."""

    def test_ask_and_answer_through_neat_sh(self):
        tmp = tempfile.mkdtemp(prefix="neat-sh-")
        try:
            work = _bootstrap_scratch_repo(tmp)
            env = dict(os.environ)
            env["PYTHON"] = sys.executable  # this interpreter already has pyto importable

            ask = subprocess.run(["bash", "pyto/scripts/neat.sh", "ask"], cwd=work, env=env,
                                  capture_output=True, text=True)
            self.assertEqual(ask.returncode, 0, ask.stderr)
            self.assertIn("[task-1] Alpha: first question", ask.stdout)

            answer = subprocess.run(
                ["bash", "pyto/scripts/neat.sh", "answer", "1", "1", "yes indeed"],
                cwd=work, env=env, capture_output=True, text=True,
            )
            self.assertEqual(answer.returncode, 0, answer.stderr)
            self.assertTrue(answer.stdout.strip().startswith("Alpha "), answer.stdout)

            answers = subprocess.run(["bash", "pyto/scripts/neat.sh", "answers"], cwd=work, env=env,
                                      capture_output=True, text=True)
            self.assertEqual(answers.returncode, 0, answers.stderr)
            self.assertIn("Alpha ", answers.stdout)
            self.assertIn(" 1 1", answers.stdout.strip())

            answer_path = os.path.join(work, "pyto", "experiments", "review", "answers", "Alpha.json")
            self.assertTrue(os.path.isfile(answer_path))
            with open(os.path.join(work, "pyto", "questions.md"), encoding="utf-8") as handle:
                self.assertIn("yes indeed", handle.read())
        finally:
            shutil.rmtree(tmp)


class OwnerFirstAndDefaults(unittest.TestCase):
    """Task 70: the batch carries what needs the owner first; a root entry that quotes him
    deciding is answered; a default is filed as the session's, never as his words."""

    def _tree(self, root: str) -> None:
        os.makedirs(os.path.join(root, "experiments", "tasks", "1"))
        os.makedirs(os.path.join(root, "experiments", "tasks", "2"))
        _write(os.path.join(root, "experiments", "tasks", "1", "packet.md"),
               "# Task 1\n\n## Uncertain\n{?} PrintForm: pretty on the terminal; a file name is the session's.\n")
        _write(os.path.join(root, "experiments", "tasks", "2", "packet.md"),
               "# Task 2\n\n## Uncertain\n{?} TickMeaning: what a chain's boundary means is the owner's to say.\n")
        _write(os.path.join(root, "questions.md"),
               "# root\n\n### {?} Decided\nOwner, 2026-09-10: \"yes\"\n\n### {?} Open\nDefault taken: none.\n")

    def test_owner_items_first_and_decided_root_entries_omitted(self):
        with tempfile.TemporaryDirectory() as root:
            self._tree(root)
            batch = review.collate({"pyto_root": root, "n": 1})
            labels = [(it["number"], it["label"], it["needs"]) for it in batch["items"]]
            self.assertEqual(labels, [(1, "TickMeaning", "owner"), (2, "Open", "root"), (3, "PrintForm", "default")])
            self.assertEqual((batch["needs_owner"], batch["root_open"], batch["defaults"]), (1, 1, 1))
            self.assertNotIn("Decided", [it["label"] for it in batch["items"]])

    def test_default_is_filed_as_the_sessions_and_leaves_the_batch(self):
        with tempfile.TemporaryDirectory() as root:
            self._tree(root)
            review.run_ask(root)
            part = review.run_answer(root, 1, 3, "pretty on the terminal, canonical on disk", kind="default")
            self.assertEqual(part["value"]["kind"], "default")
            text = open(os.path.join(root, "questions.md"), encoding="utf-8").read()
            self.assertIn('Default (session, ', text)
            self.assertIn('"pretty on the terminal, canonical on disk"', text)
            self.assertNotIn('Owner, 2026-09-10: "pretty', text)
            again = review.collate({"pyto_root": root, "n": 2})
            self.assertNotIn("PrintForm", [it["label"] for it in again["items"]])
            self.assertEqual(review.answer_for(root, "PrintForm")["kind"], "default")


if __name__ == "__main__":
    unittest.main()
