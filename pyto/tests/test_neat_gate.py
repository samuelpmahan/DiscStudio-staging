"""Executable spec of the gate at the join (task 67).

The six cases are the owner's local Blok candidate's, ported to this repository's
subject (a landing: package and head sha); the seventh and eighth are the trusted
event source (GitHub reviews, from a canned API payload, no network) and the
host (the CLI writing the gate Part into a receipt, refusing on a closed gate).
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

from pyto.neat import gate as G

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "viewer", "test"))
from record_schema import validate as validate_record  # noqa: E402

HEAD = "2f1dafe0000000000000000000000000000000ab"
SUBJECT = G.subject("task-65", HEAD, "14b0b40")


def event(**overrides):
    base = {"source": "github", "login": "samuelpmahan", "reviewDigest": G.digest(SUBJECT),
            "selection": HEAD, "disposition": "approve", "text": "Approve this exact candidate."}
    base.update(overrides)
    return base


class GateTests(unittest.TestCase):
    def test_missing_and_agent_input_stay_closed(self):
        for ev, trusted in ((None, True), (event(), False), (dict(event(), human=True), False)):
            result = G.evaluate({"subject": SUBJECT, "event": ev, "trusted": trusted})
            self.assertFalse(result["allowed"], result["reason"])

    def test_exact_human_selection(self):
        result = G.evaluate({"subject": SUBJECT, "event": event(), "trusted": True})
        self.assertTrue(result["allowed"])
        self.assertEqual(result["response"]["text"], "Approve this exact candidate.")
        self.assertEqual(result["address"], "neat.blok.gate." + G.digest(SUBJECT)[:16])
        self.assertIn("approved by samuelpmahan on 2f1dafe", result["reason"])

    def test_corrections_refusals_and_empty_input_do_not_authorize(self):
        for disposition in ("revise", "reject", "retain"):
            result = G.evaluate({"subject": SUBJECT, "event": event(disposition=disposition), "trusted": True})
            self.assertFalse(result["allowed"])
            self.assertEqual(result["response"]["disposition"], disposition, "direction is retained")
        result = G.evaluate({"subject": SUBJECT, "event": event(text="  "), "trusted": True})
        self.assertFalse(result["allowed"])
        self.assertIn("empty", result["reason"])

    def test_changed_subject_and_stale_response(self):
        changed = dict(SUBJECT, head_sha="deadbeef" + HEAD[8:])
        result = G.evaluate({"subject": changed, "event": event(), "trusted": True})
        self.assertFalse(result["allowed"])
        self.assertIn("stale", result["reason"])
        # an event re-digested for the new subject but still selecting the old head
        result = G.evaluate({"subject": changed, "event": event(reviewDigest=G.digest(changed)), "trusted": True})
        self.assertFalse(result["allowed"])
        self.assertIn("another candidate", result["reason"])

    def test_selection_must_exist(self):
        result = G.evaluate({"subject": SUBJECT, "event": event(selection="another-blok"), "trusted": True})
        self.assertFalse(result["allowed"])

    def test_green_tests_scores_and_time_are_not_inputs(self):
        ev = event(disposition="retain", suite="green", score="4/4", elapsed_ms=1)
        self.assertFalse(G.evaluate({"subject": SUBJECT, "event": ev, "trusted": True})["allowed"])

    def test_approval_naming_another_pnc_is_closed(self):
        """task 75 item 3: a subject carrying a crisp candidate's pnc additionally
        requires the approving event to name that exact pnc; the head sha alone
        is not enough once a pnc is on the subject."""
        pinned = G.subject("task-65", HEAD, "14b0b40", pnc="a" * 64)

        def pinned_event(**overrides):
            return event(reviewDigest=G.digest(pinned), **overrides)

        closed = G.evaluate({"subject": pinned, "event": pinned_event(selection_pnc="b" * 64), "trusted": True})
        self.assertFalse(closed["allowed"])
        self.assertIn("another candidate", closed["reason"])
        # the missing case: no selection_pnc at all in the event
        closed_missing = G.evaluate({"subject": pinned, "event": pinned_event(), "trusted": True})
        self.assertFalse(closed_missing["allowed"])
        opened = G.evaluate({"subject": pinned, "event": pinned_event(selection_pnc="a" * 64), "trusted": True})
        self.assertTrue(opened["allowed"])
        # a subject with no pnc at all is unaffected -- existing behavior, untouched
        unpinned = G.evaluate({"subject": SUBJECT, "event": event(), "trusted": True})
        self.assertTrue(unpinned["allowed"])

    def test_same_inputs_same_bytes(self):
        a = G.canonical(G.evaluate({"subject": SUBJECT, "event": event(), "trusted": True}))
        b = G.canonical(G.evaluate({"subject": copy.deepcopy(SUBJECT), "event": event(), "trusted": True}))
        self.assertEqual(a, b)


class GithubEventTests(unittest.TestCase):
    """The trusted source, from a canned payload: no network, no token."""

    def fake(self, url, token):
        self.urls.append(url)
        if "/pulls?" in url:
            return [{"number": 7, "head": {"ref": "exp/65", "sha": HEAD}},
                    {"number": 8, "head": {"ref": "exp/66", "sha": "ffff"}}]
        if "/pulls/7/reviews" in url:
            return [
                {"id": 1, "user": {"login": "someone-else"}, "state": "APPROVED", "commit_id": HEAD,
                 "body": "lgtm", "submitted_at": "2026-09-10T09:00:00Z"},
                {"id": 2, "user": {"login": "samuelpmahan"}, "state": "COMMENTED", "commit_id": HEAD,
                 "body": "show me the pixels", "submitted_at": "2026-09-10T09:01:00Z"},
                {"id": 3, "user": {"login": "samuelpmahan"}, "state": "APPROVED", "commit_id": "old" + HEAD[3:],
                 "body": "approve", "submitted_at": "2026-09-10T09:02:00Z"},
                {"id": 4, "user": {"login": "samuelpmahan"}, "state": "APPROVED", "commit_id": HEAD,
                 "body": "yes, this one", "submitted_at": "2026-09-10T09:03:00Z"},
            ]
        raise AssertionError("unexpected url " + url)

    def setUp(self):
        self.urls = []

    def test_newest_review_by_an_allowed_login_on_the_head_sha_is_the_event(self):
        found = G.github_event("samuelpmahan/DiscStudio-staging", "exp/65", HEAD, SUBJECT, fetch=self.fake)
        ev = found["event"]
        self.assertEqual(ev["disposition"], "approve")
        self.assertEqual(ev["text"], "yes, this one")
        self.assertEqual(ev["selection"], HEAD)
        self.assertEqual(ev["reviewDigest"], G.digest(SUBJECT))
        self.assertEqual(found["pulls"], [7])
        self.assertTrue(G.evaluate({"subject": SUBJECT, "event": ev, "trusted": True})["allowed"])

    def test_another_login_or_another_sha_is_not_an_event(self):
        found = G.github_event("samuelpmahan/DiscStudio-staging", "exp/65", HEAD, SUBJECT,
                               logins=("nobody",), fetch=self.fake)
        self.assertIsNone(found["event"])
        self.assertIn("no review by nobody", found["note"])
        found = G.github_event("samuelpmahan/DiscStudio-staging", "exp/99", HEAD, SUBJECT, fetch=self.fake)
        self.assertIsNone(found["event"])
        self.assertIn("no pull request", found["note"])


class HostTests(unittest.TestCase):
    """The CLI as land.sh calls it: the receipt gains the gate Part; a closed gate exits 3."""

    def run_cli(self, *extra, receipt=None):
        args = [sys.executable, "-m", "pyto.neat.gate", "--package", "task-65", "--head", HEAD, "--base", "14b0b40", *extra]
        if receipt:
            args += ["--receipt", receipt]
        return subprocess.run(args, capture_output=True, text=True)

    def test_mode_none_records_and_opens_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = os.path.join(tmp, "receipt.json")
            json.dump({"schema": "pyto-landing-receipt@1", "package": "task-65"}, open(receipt, "w"))
            record = os.path.join(tmp, "gate.json")
            done = self.run_cli("--mode", "none", "--record", record, receipt=receipt)
            self.assertEqual(done.returncode, 0, done.stderr)
            written = json.load(open(receipt))["gate"]
            self.assertEqual(written["mode"], "none")
            self.assertFalse(written["allowed"])
            self.assertIn("awaiting human", written["reason"])
            validate_record(json.load(open(record)))
            self.assertEqual(json.load(open(record))["ticks"][0]["invocations"][0]["calculation"]["address"],
                             "fn.neat.gate.evaluate")

    def test_stub_mode_is_never_trusted_but_exercises_the_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            approve = os.path.join(tmp, "approve.json")
            json.dump({"login": "selftest", "disposition": "approve", "selection": "<head>", "text": "stub approve"},
                      open(approve, "w"))
            done = self.run_cli("--mode", "stub:" + approve)
            self.assertEqual(done.returncode, 0, done.stderr)
            out = json.loads(done.stdout)
            self.assertFalse(out["allowed"]); self.assertFalse(out["trusted"]); self.assertTrue(out["stub_allowed"])
            reject = os.path.join(tmp, "reject.json")
            json.dump({"login": "selftest", "disposition": "reject", "selection": "<head>", "text": "no"}, open(reject, "w"))
            done = self.run_cli("--mode", "stub:" + reject)
            self.assertEqual(done.returncode, 3)
            self.assertFalse(json.loads(done.stdout)["stub_allowed"])

    def test_unknown_mode_is_refused_by_name(self):
        done = self.run_cli("--mode", "wishful")
        self.assertEqual(done.returncode, 2)
        self.assertIn("unknown mode", done.stderr)


if __name__ == "__main__":
    unittest.main()
