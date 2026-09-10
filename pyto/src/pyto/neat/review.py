"""The question loop: the owner's `{?}` marks, turned into one batch at a time.

The owner, on the frontier method (`pyto/questions.md`, `{?} TinyQuestions`):
"tailored for subagent throughput THROUGH ME. As many lil tiny questions as
possible." An agent leaves `{?} Label: description` under a packet's
"## Uncertain" whenever it was unsure; this module collates every one that is
not yet answered into a numbered batch (`neat ask`), takes the owner's reply to
one item (`neat answer <n> <k> "<words>"`), and files it in his words under that
label in `pyto/questions.md`. `neat answers` lists what has already been filed.

Four Calculations, run as one PCR named ``neat-review`` per verb
(`PCR.run(pxc, observe=True)`, so every invocation leaves a receipt and the run
leaves a `pyto-run-record@1` document -- the record is the receipt):

* ``fn.neat.review.collate`` -- pure: every unanswered `{?}` is read from the
  tree as it stands (every packet, `questions.md`, any diff Parts), so the same
  tree gives the same batch, byte for byte.
* ``oc.neat.review.captureHumanText`` -- the one effect in this module: reading
  the owner's own reply, with the clock for when. Refuses empty text.
* ``fn.tidy.freezeText`` -- pure: the sha256 of the exact bytes the owner typed.
  A different rewrite at the same address is refused; the same bytes again is
  tolerated (nothing changed).
* ``fn.neat.review.file`` -- pure given its inputs (the frozen reply, the
  technical gloss, and the tree as it stands): what to append to
  `questions.md` and the answer Part that marks the label answered. Filing
  itself -- the one real mutation of `pyto/questions.md` this module makes --
  happens here rather than through an `Effects` handle, on the same footing as
  `collate` reading the tree: both read and write the committed material the
  tree already carries, not a human's live reply or the network or the clock
  (`{?} FileIsNotAnEffect`, below, is open on whether that reading is right).

A Part on disk is one JSON file ``{"address", "value", "sha256"}`` (`sha256` is
the sha256 of the canonical JSON of `value`: ``json.dumps(value, sort_keys=True,
separators=(",", ":"))`` -- the digest rule this module reuses from
`experiments/grouped-ablation/retain.py:canonical_json`, not a second one), LF,
no timestamps inside the digested value. `captureHumanText`'s Part carries a
`recordedAt` field beside `value` (outside the digest) for exactly that reason;
it is read back from the run's own effect ledger (`Receipt.effects`), never
from a second clock read, so the value that is filed and the moment it was
filed agree by construction.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Mapping

from ..core import Calculation, Part, PxC
from ..materialize import run_record, write_record
from ..pcr import PCR

# --- addresses -------------------------------------------------------------

BATCH = "proposal.neat.batch.{n}"
CAPTURE = "neat.capture.review.{n}.{k}.response"
FREEZE = "tidy.freeze.review.{n}.{k}.response"
ANSWER = "neat.review.answer.{label}"

# --- the canonical digest (reused, not reinvented: retain.py:canonical_json) --


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest_value(value: Any) -> str:
    """sha256 of the canonical JSON of `value` -- the one digest rule, everywhere."""
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- Parts on disk -----------------------------------------------------------


def write_part(path: str, address: str, value: Any, **beside: Any) -> dict:
    """Write one Part to `path`: `{"address", "value", "sha256"}`, LF, plus `beside`.

    `beside` lands next to `value` and is never part of what `sha256` digests --
    `recordedAt` is the one field this module ever passes. Same `value`, same
    bytes, every time; sorted keys and two-space indent, like `materialize.
    write_record` writes the run record next to it.
    """
    document = {"address": address, "value": value, "sha256": digest_value(value)}
    document.update(beside)
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return document


def _read_part(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _read_lf(path: str) -> str:
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read().replace("\r\n", "\n")


# --- reading the tree: packets, questions.md, diffs, answers -----------------

QUESTION_LINE = re.compile(r"^\{\?\}\s+([^:]+):\s?(.*)$")
ROOT_LABEL = re.compile(r"\{\?\}\s+([^\s,]+)")
#: A root entry is answered when a line quotes the owner deciding or marks it resolved.
DECIDED_LINE = re.compile(r"[Oo]wner, 20\d\d|[Oo]wner \(20\d\d|^Owner[,:]|Status: resolved|\bDecided\b|\bOverturned\b|by owner")
#: A root entry still marked open carries no decision; it is open on the root, where the owner reads it,
#: and is counted rather than asked again in a batch (`bash pyto/scripts/questions.sh` lists them).
OPEN_LINE = re.compile(r"Status: open|Status: proposed")
#: The review page (task 62) read every packet up to this task; their {?} lines are the page's, not the batch's.
REVIEW_TASK_MAX = 59
#: A packet {?} line needs the owner when it says so; otherwise its stated default stands.
NEEDS_OWNER = re.compile(r"\bowner", re.I)


def split_question_line(line: str) -> tuple[str, str]:
    """`(label, text)` from one raw `{?} Label: text` line.

    The one parser for the mark, shared by `collate` (reading every packet) and
    `pyto/scripts/walk.py` (reading one packet's own lines back to show their
    answered state) -- one regex, so a line neither reads the same way twice.
    A line with no `:` has no text, only a label (the whole remainder, stripped).
    """
    match = QUESTION_LINE.match(line)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return line[len("{?}"):].strip(), ""


def _packet_dirs(tasks_dir: str) -> list[str]:
    def as_int(name: str) -> int | None:
        try:
            return int(name)
        except ValueError:
            return None

    numbered = [(as_int(d), d) for d in os.listdir(tasks_dir) if as_int(d) is not None]
    return [d for _, d in sorted(numbered)]


def _packet_items(pyto_root: str) -> list[dict]:
    """Packet-origin candidates, in stable order: task number, then line."""
    tasks_dir = os.path.join(pyto_root, "experiments", "tasks")
    items: list[dict] = []
    if not os.path.isdir(tasks_dir):
        return items
    for task_id in _packet_dirs(tasks_dir):
        packet_path = os.path.join(tasks_dir, task_id, "packet.md")
        if not os.path.isfile(packet_path):
            continue
        text = _read_lf(packet_path)
        section = text.split("\n## Uncertain", 1)[1] if "\n## Uncertain" in text else ""
        for line in section.splitlines():
            if not line.startswith("{?}"):
                continue
            label, question_text = split_question_line(line)
            if not label:
                continue
            items.append({
                "label": label, "task": f"task-{task_id}", "text": question_text,
                "origin": "packet",
                "needs": "owner" if NEEDS_OWNER.search(question_text) else "default",
            })
    return items


def _root_items(pyto_root: str) -> list[dict]:
    """Root-origin candidates: one per `### {?} Label` heading, in file order.

    `text` is the heading's own opening line of prose (most entries open on the
    question itself, e.g. `{?} PrimaryUse`; a heading with no body before the
    next one falls back to its label) -- see `{?} RootItemText`, below: the
    packet names only "the labels" as the input, and this is a reading of that,
    not the letter of it. A heading may carry several labels on one line,
    comma-separated (`### {?} PromotionScope, {?} ReceiptExport, ...` -- five
    related questions answered together); each gets its own item, all sharing
    that one heading's body text, in the order they are written on the line.
    """
    path = os.path.join(pyto_root, "questions.md")
    items: list[dict] = []
    if not os.path.isfile(path):
        return items
    lines = _read_lf(path).split("\n")
    headings = [(i, ROOT_LABEL.findall(line)) for i, line in enumerate(lines) if line.startswith("### ")]
    for i, labels in headings:
        if not labels:
            continue
        text = None
        decided = False
        marked_open = False
        for line in lines[i + 1:]:
            if line.startswith("### "):
                break
            if DECIDED_LINE.search(line):
                decided = True
            if OPEN_LINE.search(line):
                marked_open = True
            if line.strip() and text is None:
                text = line.strip()
        if decided:
            # The entry already carries the owner's decision in his words (or a resolved
            # status): it is answered on the root itself, not open ({?} RootLabelsCountAsOpen).
            continue
        for label in labels:
            items.append({"label": label, "task": "root", "text": text or label, "origin": "root",
                          "needs": "root"})  # the root is the owner's own page; counted, not re-asked
    return items


def _diff_items(pyto_root: str) -> list[dict]:
    """Diff-origin candidates: `value.remainder` of every `.../review/diffs/*.json`, by path."""
    diffs_dir = os.path.join(pyto_root, "experiments", "review", "diffs")
    items: list[dict] = []
    if not os.path.isdir(diffs_dir):
        return items
    for name in sorted(f for f in os.listdir(diffs_dir) if f.endswith(".json")):
        document = _read_part(os.path.join(diffs_dir, name))
        if not document:
            continue
        remainder = ((document.get("value") or {}).get("remainder")) or []
        for entry in remainder:
            label = (entry or {}).get("label")
            if not label:
                continue
            items.append({
                "label": label, "task": "diff", "text": (entry or {}).get("text", ""),
                "origin": "diff", "needs": "owner",
            })
    return items


REVIEW_PAGE = os.path.join("research", "decisions-to-review.md")
REVIEW_LABEL = re.compile(r"^- \*\*([^*]+)\*\*", re.M)


def _reviewed_labels(pyto_root: str) -> set[str]:
    """Labels the review page (task 62) already lists: they are the owner's to read there, not to be
    asked again in the batch; an answer under the label still removes them everywhere."""
    path = os.path.join(pyto_root, REVIEW_PAGE)
    if not os.path.isfile(path):
        return set()
    return {m.strip() for m in REVIEW_LABEL.findall(_read_lf(path))}


def _answered_labels(pyto_root: str) -> set[str]:
    answers_dir = os.path.join(pyto_root, "experiments", "review", "answers")
    if not os.path.isdir(answers_dir):
        return set()
    return {name[:-len(".json")] for name in os.listdir(answers_dir) if name.endswith(".json")}


def _existing_batch_numbers(pyto_root: str) -> list[int]:
    batches_dir = os.path.join(pyto_root, "experiments", "review", "batches")
    if not os.path.isdir(batches_dir):
        return []
    out = []
    for name in os.listdir(batches_dir):
        if name.endswith(".json") and name[:-len(".json")].isdigit():
            out.append(int(name[:-len(".json")]))
    return out


def _next_batch_number(pyto_root: str) -> int:
    existing = _existing_batch_numbers(pyto_root)
    return 1 + (max(existing) if existing else 0)


# --- fn.neat.review.collate ---------------------------------------------------


def collate(args: Mapping[str, Any]) -> dict:
    """Every unanswered `{?}` on the tree, as one numbered batch.

    Inputs, read fresh from `args["pyto_root"]` every time: the `{?}` lines
    under every packet's "## Uncertain", the labels of `questions.md`, the
    `value.remainder` of any diff Part, and which labels already have an answer
    file. Same tree, same bytes: nothing here reads a clock or a random draw.
    `args["n"]` is the batch number the caller has already claimed for this
    run's `into` address; when a caller wants the number alone (tests calling
    this Calculation directly), it defaults to one past the batches on disk.
    """
    pyto_root = args["pyto_root"]
    n = args.get("n")
    if n is None:
        n = _next_batch_number(pyto_root)
    answered = _answered_labels(pyto_root)
    items = [
        item for item in (
            *_packet_items(pyto_root), *_root_items(pyto_root), *_diff_items(pyto_root),
        )
        if item["label"] not in answered
    ]
    reviewed = _reviewed_labels(pyto_root)
    for item in items:
        task_number = int(item["task"].split("-")[1]) if item["task"].startswith("task-") else None
        if item["label"] in reviewed or (reviewed and task_number is not None and task_number <= REVIEW_TASK_MAX):
            item["needs"] = "reviewed"
    # What needs the owner first, then what the review page already lists, then what carries a
    # default; each group in source order.
    rank = {"owner": 0, "root": 1, "reviewed": 2, "default": 3}
    items = sorted(items, key=lambda it: rank.get(it.get("needs", "default"), 2))
    for number, item in enumerate(items, start=1):
        item["number"] = number
    ordered = [
        {"number": item["number"], "label": item["label"], "task": item["task"],
         "text": item["text"], "origin": item["origin"], "needs": item.get("needs", "default")}
        for item in items
    ]
    return {"n": n, "items": ordered,
            "needs_owner": sum(1 for it in ordered if it["needs"] == "owner"),
            "reviewed": sum(1 for it in ordered if it["needs"] == "reviewed"),
            "root_open": sum(1 for it in ordered if it["needs"] == "root"),
            "defaults": sum(1 for it in ordered if it["needs"] == "default")}


COLLATE = Calculation("fn.neat.review.collate", collate)


# --- oc.neat.review.captureHumanText ------------------------------------------


def capture_human_text(args: Mapping[str, Any]) -> dict:
    """The owner's exact reply to one batch item, plus when it was captured.

    Refuses empty or whitespace-only text, naming the item. The clock is read
    once, through the run's `Effects` handle, so it lands on the receipt's
    ledger (`Receipt.effects`) and not only in this return value -- the caller
    reads `recordedAt` back from there and keeps it out of the digested value
    (module docstring), rather than this Calculation splitting its own return
    into two shapes.
    """
    n, k, label, text = args["n"], args["k"], args["label"], args["text"]
    if not isinstance(text, str) or text.strip() == "":
        raise ValueError(
            f"oc.neat.review.captureHumanText: item {k} of batch {n} ({label!r}) got "
            "empty text; the owner's reply may not be blank"
        )
    recorded_at = args["effects"].now_ms()
    return {"n": n, "k": k, "label": label, "text": text, "recordedAt": recorded_at}


CAPTURE_HUMAN_TEXT = Calculation("oc.neat.review.captureHumanText", capture_human_text)


# --- fn.tidy.freezeText --------------------------------------------------------


def freeze_text(args: Mapping[str, Any]) -> dict:
    """The sha256 of a capture's exact text, refusing a rewrite that changes it.

    `args["existing"]` is the value already on disk at this freeze's address,
    when there is one -- an ordinary Part read the caller binds only when
    `PxC.has` says it is there, exactly like any other input this run consumes.
    The same bytes again is not a rewrite; a different rewrite is refused by
    name, naming both digests.
    """
    capture = args["capture"]
    text = capture["text"]
    digest = _sha256_text(text)
    existing = args.get("existing")
    if existing is not None and existing.get("bytes") != text:
        raise ValueError(
            f"fn.tidy.freezeText: tidy.freeze.review.{capture['n']}.{capture['k']}.response "
            f"is already frozen ({existing.get('sha256')}); a different rewrite ({digest}) "
            "is refused -- the same bytes again would be tolerated"
        )
    return {"sha256": digest, "bytes": text}


FREEZE_TEXT = Calculation("fn.tidy.freezeText", freeze_text)


# --- fn.neat.review.file -------------------------------------------------------


def _file_section(text: str, label: str, lines: list[str]) -> str:
    """`text` with `lines` filed under `### {?} label`, creating the section at the
    end when the label is new. Matches the file's own convention: one blank
    line between sections, none between the lines inside one (`questions.md`,
    e.g. `{?} WhatIsATick`'s three "Owner, ..." lines back to back)."""
    if not text.endswith("\n"):
        text += "\n"
    heading = f"### {{?}} {label}"
    heading_pattern = re.compile(r"^" + re.escape(heading) + r"$", re.M)
    match = heading_pattern.search(text)
    block = "\n".join(lines)
    if match is None:
        body = text.rstrip("\n")
        return f"{body}\n\n{heading}\n{block}\n"
    body_start = match.end() + 1  # past the heading line's own newline
    next_heading = re.search(r"^### ", text[body_start:], re.M)
    if next_heading:
        section_end = body_start + next_heading.start()
        section_body = text[body_start:section_end].rstrip("\n")
        return f"{text[:body_start]}{section_body}\n{block}\n\n{text[section_end:]}"
    section_body = text[body_start:].rstrip("\n")
    return f"{text[:body_start]}{section_body}\n{block}\n"


def file_answer(args: Mapping[str, Any]) -> dict:
    """File the frozen reply under its label in `questions.md`; return the answer Part's value.

    `args["date"]` is not read here -- it is derived by the caller from the
    capture's own `recordedAt` (module docstring: "the date comes from the
    capture's recordedAt, not from the clock") and handed in as `args["capture"]`
    itself, so this Calculation stays a function of its bound inputs. Refiling
    the identical (n, k, digest) a second time is a no-op on `questions.md`
    (the marker line is searched for first) -- the answer Part it returns is
    the same value either way.
    """
    frozen = args["frozen"]
    capture = args["capture"]
    label, n, k = args["label"], args["n"], args["k"]
    technical = args.get("technical")
    pyto_root = args["pyto_root"]
    date = datetime.fromtimestamp(capture["recordedAt"] / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")

    kind = args.get("kind") or "owner"
    marker = f"Filed from batch {n} item {k}, frozen {frozen['sha256'][:12]}" + ("" if kind == "owner" else f" ({kind})")
    if kind == "owner":
        lines = [f'Owner, {date}: "{frozen["bytes"]}"']
    else:
        # The session's default, never the owner's words: it stands until he says otherwise.
        lines = [f'Default (session, {date}): "{frozen["bytes"]}"']
    if technical:
        lines.append(f"Technical: {technical}")
    lines.append(marker)

    questions_path = os.path.join(pyto_root, "questions.md")
    text = _read_lf(questions_path) if os.path.isfile(questions_path) else "# {?} The root\n"
    if marker not in text:
        text = _file_section(text, label, lines)
        with open(questions_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)

    return {"label": label, "n": n, "k": k, "sha256": frozen["sha256"], "kind": kind}


FILE = Calculation("fn.neat.review.file", file_answer)


# --- the two verbs as observed PCR runs ---------------------------------------


def _runs_dir(pyto_root: str) -> str:
    return os.path.join(pyto_root, "experiments", "review", "runs")


def run_ask(pyto_root: str) -> dict:
    """`neat ask`: collate, publish the batch Part, leave the run record."""
    n = _next_batch_number(pyto_root)
    batch_address = BATCH.format(n=n)
    pxc = PxC()
    pcr = PCR("neat-review")
    pcr.calc("Collate", COLLATE, id="collate", into=batch_address, args={"pyto_root": pyto_root, "n": n})
    run = pcr.run(pxc, observe=True)
    record = run_record(run, pxc, preexisting=set())
    write_record(record, os.path.join(_runs_dir(pyto_root), f"ask-{n}.json"))
    return write_part(
        os.path.join(pyto_root, "experiments", "review", "batches", f"{n}.json"),
        batch_address, run.results["collate"],
    )


def run_answer(pyto_root: str, n: int, k: int, text: str, technical: str | None = None,
               kind: str = "owner") -> dict:
    """`neat answer <n> <k> "<words>"` (kind owner) or `neat default ...` (kind default):
    capture, freeze, file; one run record."""
    batch = _read_part(os.path.join(pyto_root, "experiments", "review", "batches", f"{n}.json"))
    if batch is None:
        raise ValueError(f"neat answer: no batch {n} on disk; run 'neat ask' first")
    item = next((it for it in batch["value"]["items"] if it["number"] == k), None)
    if item is None:
        raise ValueError(f"neat answer: batch {n} has no item {k}")
    label = item["label"]

    capture_address = CAPTURE.format(n=n, k=k)
    freeze_address = FREEZE.format(n=n, k=k)
    answer_address = ANSWER.format(label=label)

    pxc = PxC()
    freeze_path = os.path.join(pyto_root, "experiments", "review", "freezes", f"{n}-{k}.json")
    existing_freeze = _read_part(freeze_path)
    if existing_freeze is not None:
        pxc.set(freeze_address, existing_freeze["value"])
    preexisting = set(pxc.addresses())

    pcr = PCR("neat-review")
    capture_ref = pcr.calc(
        "Capture", CAPTURE_HUMAN_TEXT, id="capture", into=capture_address,
        args={"n": n, "k": k, "label": label, "text": text},
    )
    freeze_inputs: dict[str, Any] = {"capture": capture_ref}
    if pxc.has(freeze_address):
        freeze_inputs["existing"] = Part(freeze_address)
    freeze_ref = pcr.calc("Freeze", FREEZE_TEXT, id="freeze", into=freeze_address, **freeze_inputs)
    pcr.calc(
        "File", FILE, id="file", into=answer_address,
        frozen=freeze_ref, capture=capture_ref,
        args={"label": label, "n": n, "k": k, "technical": technical, "pyto_root": pyto_root,
              "kind": kind},
    )

    effects_root = os.path.join(pyto_root, "experiments", "review")
    run = pcr.run(pxc, observe=True, effects_root=effects_root)

    record = run_record(run, pxc, preexisting=preexisting)
    write_record(record, os.path.join(_runs_dir(pyto_root), f"{'answer' if kind == 'owner' else 'default'}-{n}-{k}.json"))

    capture_value = dict(run.results["capture"])
    recorded_at = capture_value.pop("recordedAt")
    write_part(
        os.path.join(pyto_root, "experiments", "review", "captures", f"{n}-{k}.json"),
        capture_address, capture_value, recordedAt=recorded_at,
    )
    write_part(freeze_path, freeze_address, run.results["freeze"])
    return write_part(
        os.path.join(pyto_root, "experiments", "review", "answers", f"{label}.json"),
        answer_address, run.results["file"],
    )


def answer_for(pyto_root: str, label: str) -> dict | None:
    """The filed answer's value for `label`, or None -- what `walk.py` shows per step."""
    document = _read_part(os.path.join(pyto_root, "experiments", "review", "answers", f"{label}.json"))
    return document["value"] if document else None


def list_answers(pyto_root: str) -> list[dict]:
    """Every filed answer's value, one per label, sorted by label."""
    answers_dir = os.path.join(pyto_root, "experiments", "review", "answers")
    if not os.path.isdir(answers_dir):
        return []
    out = []
    for name in sorted(f for f in os.listdir(answers_dir) if f.endswith(".json")):
        document = _read_part(os.path.join(answers_dir, name))
        if document:
            out.append(document["value"])
    return out


# --- the CLI: python -m pyto.neat.review ask|answer|answers -------------------


def default_pyto_root() -> str:
    """The `pyto/` directory this process is meant to act on: its own working directory.

    Every verb elsewhere in `pyto/scripts/neat.sh` that shells out to Python
    `cd`s into the directory its relative paths mean first (`cmd_pack`,
    `cmd_land`); `neat ask`/`neat answer`/`neat answers` do the same, so this
    module never has to guess a root and a scratch-tree round trip (test (g))
    needs nothing more than a different current directory.
    """
    return os.getcwd()


def _print_batch(batch_value: dict) -> None:
    items = batch_value["items"]
    owner = [it for it in items if it.get("needs") == "owner"]
    reviewed = [it for it in items if it.get("needs") == "reviewed"]
    root_open = [it for it in items if it.get("needs") == "root"]
    defaults = [it for it in items if it.get("needs") == "default"]
    n = batch_value["n"]
    print(f"batch {n}: {len(owner)} need you; {len(root_open)} open on the root since before the loop; "
          f"{len(reviewed)} are on the review page (research/decisions-to-review.md); "
          f"{len(defaults)} carry a default that stands until you say otherwise")
    if owner:
        print("\nNeed you (neat answer %d <number> \"<words>\"):" % n)
        for item in owner:
            print(f"{item['number']}. [{item['task']}] {item['label']}: {item['text']}")
    if root_open:
        print(f"\nOpen on the root since before the loop, not asked again here: {len(root_open)} labels "
              f"(bash pyto/scripts/questions.sh lists them; neat answer {n} <number> still files one).")
    if reviewed:
        print(f"\nOn the review page, not asked again here: {len(reviewed)} labels (neat answer {n} <number> still files one).")
    if defaults:
        print("\nDefaults, standing (neat default %d <number> \"<sentence>\" files one; answer it to overturn):" % n)
        for item in defaults:
            print(f"{item['number']}. [{item['task']}] {item['label']}: {item['text']}")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    pyto_root = default_pyto_root()
    if not argv:
        print("usage: python -m pyto.neat.review ask|answer|default|answers", file=sys.stderr)
        return 2
    verb, rest = argv[0], argv[1:]
    if verb == "ask":
        part = run_ask(pyto_root)
        _print_batch(part["value"])
        return 0
    if verb in ("answer", "default"):
        if len(rest) < 3:
            print(f'usage: neat {verb} <n> <k> "<words>" [--technical "<text>"]', file=sys.stderr)
            return 2
        try:
            n, k = int(rest[0]), int(rest[1])
        except ValueError:
            print("neat answer: <n> and <k> must be numbers", file=sys.stderr)
            return 2
        text = rest[2]
        technical = None
        tail = rest[3:]
        if tail[:1] == ["--technical"]:
            technical = tail[1] if len(tail) > 1 else ""
        try:
            part = run_answer(pyto_root, n, k, text, technical=technical,
                              kind="owner" if verb == "answer" else "default")
        except ValueError as refused:
            print(f"neat {verb}: {refused}", file=sys.stderr)
            return 1
        value = part["value"]
        print(f"{value['label']} {value['sha256']} {value.get('kind', 'owner')}")
        return 0
    if verb == "answers":
        for value in list_answers(pyto_root):
            print(f"{value['label']} {value['sha256']} {value['n']} {value['k']} {value.get('kind', 'owner')}")
        return 0
    print(f"python -m pyto.neat.review: unknown verb {verb!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
