"""The join asks once, and only a human can open it.

Two Calculations and the host discipline around them.

``fn.neat.gate.evaluate`` is pure: a landing's *subject* (package and the exact
head sha of the candidate, which fixes every byte the landing would join), a
*frozen event* (what a person said about that exact subject), and whether the
host trusts the event's source, in; ``neat.blok.gate.<digest>`` out, ``allowed``
only when the event is trusted, names this subject's digest, carries non-empty
text, and its disposition is ``approve`` of this exact head sha.  ``revise``,
``reject`` and ``retain`` are kept as direction and keep the join closed.  A
missing event, an agent-written event, a stale digest, whitespace, or an
approval of another candidate stay closed.  Green tests, scores, labels and
elapsed time are not inputs and cannot open it.

``oc.neat.gate.githubReview`` is the one trusted event source this repository
has: a pull request review on the candidate branch, by an allowed login, whose
``commit_id`` is the head sha.  A worker in this sandbox cannot write a review
under the owner's GitHub login, which is what makes the event trusted; the gate
itself authenticates nobody.  The token is read from ``GITHUB_TOKEN`` (or
``GH_TOKEN``) with ``os.environ`` and never through the effects handle, because
``Effects.env`` records the value it reads and a token must not be in a record
(``{?} SecretsAreNotEffects``).  The requests themselves are not ledgered
either: the handle has no network verb (``{?} HttpIsNotAnEffectKind``); the
handle records the clock read that stamps the event.

``land.sh`` step 4b calls ``python -m pyto.neat.gate`` after the receipt is
written and before the commit, when ``.neat/gate`` (or ``$NEAT_GATE``) names a
mode: ``github`` (trusted), ``stub:<event.json>`` (a canned event for the
selftest, recorded as untrusted: it can never open a landing the receipt would
call approved), or nothing (the default today: the receipt says ``mode: none``
and the walk says ``unapproved``).  The receipt's ``gate`` field is the Part.

Addresses follow ``context-stream/NEAT-SELF-CLEANING-KNOWLEDGE-GRAPH.yaml``
(``neat.blok.gate.<reviewDigest>``); ``address.py`` reads ``neat`` as a mount
outside the address and enforces nothing, so the spelling is kept as the owner's
local system spells it (``{?} NeatIsAMount``).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping

from pyto import Calculation, PCR, Part, PxC
from pyto.materialize import run_record, write_record

DISPOSITIONS = ("approve", "revise", "reject", "retain")
STATE_TO_DISPOSITION = {"APPROVED": "approve", "CHANGES_REQUESTED": "reject", "COMMENTED": "retain"}
DEFAULT_LOGINS = ("samuelpmahan",)


# --- digests: the one rule (grouped-ablation/retain.py) -----------------------------

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def subject(package: str, head_sha: str, base_sha: str | None = None) -> dict[str, Any]:
    """What a landing would join: the package and the exact candidate head.

    The head sha fixes every byte of the candidate, including its packet (the
    review text) and its claimed files, so it is the frozen subject; the
    receipt's per-file digests are derived from it.
    """
    if not package or not head_sha:
        raise ValueError("a gate subject needs a package and a head sha")
    return {"kind": "landing", "package": package, "head_sha": head_sha, "base_sha": base_sha}


# --- fn.neat.gate.evaluate ----------------------------------------------------------

def evaluate(args: Mapping[str, Any]) -> dict[str, Any]:
    """Decide one gate.  Pure: nothing here reads the world."""
    subj = dict(args["subject"])
    event = args.get("event")
    trusted = bool(args.get("trusted", False))
    review = digest(subj)
    out: dict[str, Any] = {
        "address": f"neat.blok.gate.{review[:16]}",
        "reviewDigest": review,
        "subject": subj,
        "allowed": False,
        "trusted": trusted,
        "reason": "",
        "response": None,
    }
    if event is None:
        out["reason"] = "awaiting human: no event"
        return out
    if not isinstance(event, Mapping):
        out["reason"] = "not an event"
        return out
    response = {
        "text": event.get("text"),
        "disposition": event.get("disposition"),
        "selection": event.get("selection"),
        "login": event.get("login"),
        "source": event.get("source"),
    }
    if not trusted:
        out["reason"] = "not a trusted event: the host did not vouch for its source"
        return out
    if event.get("reviewDigest") != review:
        out["reason"] = "stale: the event names another subject"
        return out
    text = response["text"]
    if not isinstance(text, str) or not text.strip():
        out["reason"] = "empty response: whitespace is not an answer"
        return out
    out["response"] = response
    disposition = response["disposition"]
    if disposition not in DISPOSITIONS:
        out["reason"] = f"unknown disposition {disposition!r}"
        return out
    if disposition != "approve":
        out["reason"] = f"{disposition}: direction retained, joining closed"
        return out
    if response["selection"] != subj["head_sha"]:
        out["reason"] = "approve names another candidate"
        return out
    out["allowed"] = True
    out["reason"] = f"approved by {response['login']} on {subj['head_sha'][:7]}"
    return out


EVALUATE = Calculation("fn.neat.gate.evaluate", evaluate)


# --- oc.neat.gate.githubReview ------------------------------------------------------

def _urlopen_json(url: str, token: str | None) -> Any:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "pyto-neat-gate",
        **({"Authorization": f"Bearer {token}"} if token else {}),
    })
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 (api.github.com only)
        return json.loads(response.read().decode("utf-8"))


def github_event(repo: str, branch: str, head_sha: str, subj: Mapping[str, Any],
                 logins: tuple[str, ...] = DEFAULT_LOGINS,
                 fetch: Callable[[str, str | None], Any] | None = None,
                 token: str | None = None) -> dict[str, Any]:
    """The newest review by an allowed login on the exact head sha, as a frozen event.

    Returns ``{"event": <event or None>, "note": <why None>, "pulls": [numbers]}``.
    """
    fetch = fetch or _urlopen_json
    owner = repo.split("/")[0]
    base = f"https://api.github.com/repos/{repo}"
    pulls = fetch(f"{base}/pulls?head={owner}:{branch}&state=all&per_page=20", token)
    numbers = [p["number"] for p in pulls if (p.get("head") or {}).get("ref") == branch]
    if not numbers:
        return {"event": None, "note": f"no pull request with head {branch}", "pulls": []}
    found: list[dict[str, Any]] = []
    for number in numbers:
        for review in fetch(f"{base}/pulls/{number}/reviews?per_page=100", token):
            login = (review.get("user") or {}).get("login")
            if login not in logins or review.get("commit_id") != head_sha:
                continue
            disposition = STATE_TO_DISPOSITION.get(review.get("state"))
            if disposition is None:
                continue
            found.append({
                "source": "github",
                "login": login,
                "reviewDigest": digest(dict(subj)),
                "selection": head_sha,
                "disposition": disposition,
                "text": review.get("body") or "",
                "submitted_at": review.get("submitted_at"),
                "review_id": review.get("id"),
                "pull": number,
            })
    if not found:
        return {"event": None, "note": f"no review by {', '.join(logins)} on {head_sha[:7]}", "pulls": numbers}
    found.sort(key=lambda e: (e["submitted_at"] or "", e["review_id"] or 0))
    return {"event": found[-1], "note": "", "pulls": numbers}


def github_review(args: Mapping[str, Any]) -> dict[str, Any]:
    """oc.neat.gate.githubReview: the frozen event from GitHub, stamped by the handle's clock."""
    effects = args["effects"]
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")  # never through the handle
    result = github_event(args["repo"], args["branch"], args["head_sha"], args["subject"],
                          tuple(args.get("logins") or DEFAULT_LOGINS), token=token)
    result["fetched_ms"] = effects.now_ms()
    return result


GITHUB_REVIEW = Calculation("oc.neat.gate.githubReview", github_review)


# --- the host: modes, the PCR, the record -------------------------------------------

def read_mode(root: str) -> str:
    env = os.environ.get("NEAT_GATE")
    if env:
        return env.strip()
    path = os.path.join(root, ".neat", "gate")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            return handle.read().strip() or "none"
    return "none"


def stub_event(path: str, subj: Mapping[str, Any]) -> dict[str, Any]:
    """A canned event for the selftest.  Its reviewDigest is filled in for the caller's
    subject so the stub tests the gate's logic and not the digest; it is never trusted."""
    with open(path, encoding="utf-8") as handle:
        event = json.load(handle)
    event.setdefault("source", "stub")
    event["reviewDigest"] = digest(dict(subj))
    if event.get("selection") == "<head>":
        event["selection"] = subj["head_sha"]
    return event


def run_gate(subj: Mapping[str, Any], event: Mapping[str, Any] | None, trusted: bool,
             record_path: str | None = None) -> dict[str, Any]:
    """Evaluate through a PCR so the decision leaves a receipt and a run record."""
    pxc = PxC()
    pxc.set("neat.gate.subject", dict(subj))
    pxc.set("neat.gate.event", dict(event) if event is not None else None)
    pcr = PCR("neat-gate")
    pcr.calc("Gate", EVALUATE, id="evaluate",
             into=Part(f"neat.blok.gate.{digest(dict(subj))[:16]}"),
             args={"subject": dict(subj), "event": dict(event) if event is not None else None,
                   "trusted": bool(trusted)})
    run = pcr.run(pxc, observe=True)
    if record_path:
        write_record(run_record(run, pxc), record_path)
    return run.results["evaluate"]


def main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pyto.neat.gate")
    parser.add_argument("--package", required=True)
    parser.add_argument("--head", required=True, help="the candidate head sha")
    parser.add_argument("--base", default=None)
    parser.add_argument("--mode", default=None, help="github | stub:<event.json> | none (default: .neat/gate or $NEAT_GATE)")
    parser.add_argument("--repo", default=None, help="owner/name (default: from origin)")
    parser.add_argument("--branch", default=None, help="the candidate branch (default: exp/<n> from the package)")
    parser.add_argument("--logins", default=",".join(DEFAULT_LOGINS))
    parser.add_argument("--receipt", default=None, help="receipt.json to write the gate Part into")
    parser.add_argument("--record", default=None, help="where to write the gate's run record")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    mode = args.mode or read_mode(args.root)
    subj = subject(args.package, args.head, args.base)
    event, trusted, note = None, False, ""
    if mode == "github":
        repo = args.repo or _origin_repo(args.root)
        branch = args.branch or ("exp/" + args.package.split("-", 1)[-1])
        fetched = github_event(repo, branch, args.head, subj, tuple(args.logins.split(",")),
                               token=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
        event, note, trusted = fetched["event"], fetched["note"], fetched["event"] is not None
    elif mode.startswith("stub:"):
        event, trusted, note = stub_event(mode[5:], subj), False, "stub event: recorded, never trusted"
    elif mode != "none":
        print(f"gate: unknown mode {mode!r}", file=sys.stderr)
        return 2
    result = run_gate(subj, event, trusted, args.record)
    result["mode"] = mode
    if note:
        result["note"] = note
    if mode.startswith("stub:"):
        # The selftest needs the allowed path exercised; a stub may open the gate in the
        # receipt only as `allowed` with `trusted: false`, which the walk prints as such.
        stub_allowed = evaluate({"subject": subj, "event": event, "trusted": True})["allowed"]
        result["stub_allowed"] = stub_allowed
    if args.receipt:
        with open(args.receipt, encoding="utf-8") as handle:
            receipt = json.load(handle)
        receipt["gate"] = result
        with open(args.receipt, "w", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2)
    print(canonical(result))
    if mode == "none":
        return 0
    opened = result["allowed"] or (mode.startswith("stub:") and result.get("stub_allowed"))
    return 0 if opened else 3


def _origin_repo(root: str) -> str:
    import subprocess

    url = subprocess.run(["git", "-C", root, "remote", "get-url", "origin"],
                         capture_output=True, text=True).stdout.strip()
    url = url.removesuffix(".git")
    for marker in ("github.com/", "github.com:"):
        if marker in url:
            return url.split(marker, 1)[1]
    raise SystemExit(f"gate: origin is not a GitHub remote: {url!r}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
