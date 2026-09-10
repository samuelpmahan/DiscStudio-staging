"""The tutoring page, read off one desk's own record.

    python tutor.py <desk-repo-dir> > tutor.html

The owner, on why a tutoring agent should never read a profile (pyto/questions.md,
`{?} Students`): "personal parts and calculations let the agent learn how the
student learns ... a student's own mount holds their Parts and the Calculations they
wrote, so a tutoring agent reads how they learn from their own records (what they
retry, where they write `{?}`, what they undo, how long a Tick takes them), never
from a profile."

So this page has exactly four sources, all of them files the student's own desk
already keeps, and no fifth:

  .neat/landings/<stamp>-<package>/receipt.json   what was verified, and what it scored
  .neat/landings/failed/<stamp>-<package>.json    what was refused, and why
  .neat/BOARD.md, under "## Today"                started, landed, refused, killed, undo
  <task packets>/packet.md                        the `{?}` lines they wrote
  submissions/*/evidence/*/record.json            how long each Tick took them

Nothing is inferred about the person. Every line on the page points at a file and a
number that was already there, which is also what makes the page checkable: it is a
pure function of the desk. No clock is read while rendering, every list is sorted by
something in the data, and no absolute path is printed -- so running it twice on the
same desk gives byte-identical HTML, and a diff between two runs is a change in the
desk, never in the renderer.

The caveat this page inherits from the assignment it belongs to: a record shows what
a student did, not whether they understood it. Nothing here is a grade.
"""

from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
import sys

# --- reading the desk ------------------------------------------------------------

# `- 2026-09-10 02:40 **landed** `task-1` score 2/2: a page of my own questions (...)`
BOARD_LINE = re.compile(
    r"^- (?P<stamp>\d{4}-\d\d-\d\d \d\d:\d\d) "
    r"\*\*(?P<kind>[a-z]+)\*\* `(?P<package>[^`]+)`"
    r"(?: score (?P<passed>\d+)/(?P<total>\d+))?"
    r": (?P<text>.*)$"
)

# A `{?}` line, in the two spellings the record uses: the packet's own
# `{?} Label: ...`, and a hand-off page's `- `{?}` ...` bullet. Both have to start
# the line. That is what keeps the packet template's own explanation of the habit
# -- which opens with a backtick -- from being counted as a question somebody wrote.
QUESTION_LINES = (
    re.compile(r"^\{\?\} (?P<text>.+?)\s*$"),
    re.compile(r"^[-*] `\{\?\}`\s*(?P<text>.+?)\s*$"),
)

SKIP_DIRS = (".git", "tools", "node_modules", "__pycache__")


def relative(desk: str, path: str) -> str:
    """A path inside the desk, as the desk sees it. Never an absolute path."""
    return os.path.relpath(path, desk).replace(os.sep, "/")


def scrub(desk: str, text: str) -> str:
    """Take the desk's own location back out of a line the record wrote.

    A refusal's reason names the verifier output by absolute path, because land.sh
    wrote it on the machine the student was sitting at. That path is where the desk
    happens to live today, not something about the work, and it would put a temp
    directory on a page that is supposed to be a function of the desk alone.
    """
    for root in (os.path.abspath(desk), os.path.realpath(desk)):
        text = text.replace(root + os.sep, "").replace(root, ".")
    return text


def read_json(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def board_lines(desk: str) -> list[dict]:
    """The Today lines, oldest first (the board writes newest first)."""
    path = os.path.join(desk, ".neat", "BOARD.md")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if "## Today" not in text:
        return []
    found = []
    for line in text.split("## Today", 1)[1].splitlines():
        match = BOARD_LINE.match(line.rstrip())
        if not match:
            continue
        entry = match.groupdict()
        entry["text"] = scrub(desk, entry["text"])
        entry["undo"] = entry["package"].startswith("undo-")
        entry["task"] = entry["package"][len("undo-"):] if entry["undo"] else entry["package"]
        found.append(entry)
    found.reverse()
    return found


def receipts(desk: str) -> list[dict]:
    """Every landing receipt the desk kept, verified and failed, sorted by id.

    The id opens with the stamp the landing was made at, so sorting by it is
    chronological without reading a clock or a file's modification time.
    """
    found = []
    for path in sorted(glob.glob(os.path.join(desk, ".neat", "landings", "*", "receipt.json"))):
        data = read_json(path)
        score = data.get("score") or {}
        found.append({
            "id": data.get("id", ""),
            "package": data.get("package", ""),
            "result": data.get("result", ""),
            "passed": score.get("passed"),
            "total": score.get("total"),
            "verifier": (data.get("verifier") or {}).get("command"),
            "reason": "",
            "path": relative(desk, path),
        })
    for path in sorted(glob.glob(os.path.join(desk, ".neat", "landings", "failed", "*.json"))):
        data = read_json(path)
        found.append({
            "id": data.get("id", ""),
            "package": data.get("package", ""),
            "result": data.get("result", "failed"),
            "passed": None,
            "total": None,
            "verifier": None,
            "reason": scrub(desk, data.get("reason", "")),
            "path": relative(desk, path),
        })
    found.sort(key=lambda entry: (entry["id"], entry["path"]))
    return found


def walk_files(desk: str, name: str) -> list[str]:
    """Every file called <name> under the desk, sorted, skipping what is not theirs."""
    found = []
    for root, directories, names in os.walk(desk):
        directories[:] = sorted(d for d in directories if d not in SKIP_DIRS)
        if name in names:
            found.append(os.path.join(root, name))
    return sorted(found)


def packets(desk: str) -> list[dict]:
    """The task packets on this desk: the landed ones and the ones still open."""
    found = []
    for path in walk_files(desk, "packet.md"):
        if os.sep + ".neat" + os.sep + "tasks" + os.sep not in path:
            continue
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        intent = re.search(r"^Intent: (.*)$", text, re.M)
        verify = re.search(r"^Verify: (.*)$", text, re.M)
        rel = relative(desk, path)
        found.append({
            "path": rel,
            "task": os.path.basename(os.path.dirname(path)),
            "open": rel.startswith("EXP/"),
            "intent": intent.group(1).strip() if intent else "(no intent line)",
            "verify": verify.group(1).strip() if verify else "none",
        })
    found.sort(key=lambda entry: (entry["task"], entry["path"]))
    return found


def questions(desk: str) -> list[dict]:
    """Every `{?}` line on the desk, by file, in the order the file has them."""
    found = []
    seen = set()
    # The packet is the source of a task's `{?}` lines; neat copies them onto the
    # hand-off page it generates beside it, so counting both would count each
    # question twice. A hand-off the student wrote themselves -- the one inside the
    # submission -- is not that copy, and stays.
    candidates = walk_files(desk, "packet.md") + [
        path
        for name in ("questions.md", "HANDOFF.md")
        for path in walk_files(desk, name)
        if os.sep + ".neat" + os.sep + "tasks" + os.sep not in path
    ]
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        for number, line in enumerate(lines, start=1):
            for pattern in QUESTION_LINES:
                match = pattern.match(line)
                if match:
                    found.append({
                        "path": relative(desk, path),
                        "line": number,
                        "text": scrub(desk, match.group("text")),
                    })
                    break
    found.sort(key=lambda entry: (entry["path"], entry["line"]))
    return found


def runs(desk: str) -> list[dict]:
    """The run records under the submissions, with per-Tick work and latency.

    Two numbers per Tick, and they are different questions (pyto/questions.md,
    `{?} TicksAsCircuits`): the Calculations inside one Tick are parallel branches,
    so their durations *add* into the work the Tick did, while the time it would take
    is the longest single branch. A Tick where the two differ is a Tick that could
    have run side by side, which is the arithmetic the student's own hand-off claims.
    """
    found = []
    for path in sorted(walk_files(desk, "record.json")):
        rel = relative(desk, path)
        if "/evidence/" not in rel or "/submissions/" not in rel:
            continue
        try:
            record = read_json(path)
        except (OSError, ValueError):
            continue
        if not isinstance(record, dict) or "ticks" not in record:
            continue
        ticks = []
        for tick in record["ticks"]:
            durations = [
                float(invocation.get("duration_ms") or 0.0)
                for invocation in tick.get("invocations", [])
            ]
            ticks.append({
                "name": tick.get("name", "?"),
                "index": tick.get("index"),
                "calculations": [invocation.get("id", "?") for invocation in tick.get("invocations", [])],
                "work": sum(durations),
                "latency": max(durations) if durations else 0.0,
            })
        found.append({
            "path": rel,
            "ticks": ticks,
            "invocations": (record.get("counters") or {}).get("invocations"),
            "hits": (record.get("counters") or {}).get("hits"),
        })
    return found


def read_desk(desk: str) -> dict:
    """Everything the page is a function of, and nothing else."""
    return {
        "name": os.path.basename(os.path.abspath(desk.rstrip(os.sep))) or "desk",
        "board": board_lines(desk),
        "receipts": receipts(desk),
        "packets": packets(desk),
        "questions": questions(desk),
        "runs": runs(desk),
    }


# --- what the record says about how they work -------------------------------------


def retried(data: dict) -> list[dict]:
    """Tasks that were refused and then landed: the same task, twice or more."""
    attempts: dict[str, list[dict]] = {}
    order: list[str] = []
    for entry in data["board"]:
        if entry["kind"] not in ("refused", "landed") or entry["undo"]:
            continue
        if entry["package"] not in attempts:
            attempts[entry["package"]] = []
            order.append(entry["package"])
        attempts[entry["package"]].append(entry)
    out = []
    for package in order:
        tries = attempts[package]
        if any(t["kind"] == "refused" for t in tries) and any(t["kind"] == "landed" for t in tries):
            out.append({"package": package, "tries": tries})
    return out


def undone(data: dict) -> list[dict]:
    """Landings the student took back out again, newest last."""
    return [entry for entry in data["board"] if entry["undo"] and entry["kind"] == "landed"]


def scored(data: dict) -> list[dict]:
    """Every score on the desk: which package, which verdict, which verifier."""
    out = []
    for entry in data["board"]:
        if entry["passed"] is None:
            continue
        # A refusal leaves a failed receipt with no score in it (land.sh writes the
        # score onto the board and the reason into the receipt), so the two verdicts
        # are matched to their receipts by different keys on purpose.
        if entry["kind"] == "refused":
            receipt = next(
                (r for r in data["receipts"]
                 if r["package"] == entry["package"] and r["result"] == "failed"),
                None,
            )
        else:
            receipt = next(
                (r for r in data["receipts"]
                 if r["package"] == entry["package"] and str(r["passed"]) == entry["passed"]),
                None,
            )
        out.append({
            "package": entry["package"],
            "kind": entry["kind"],
            "passed": int(entry["passed"]),
            "total": int(entry["total"]),
            "verifier": (receipt["verifier"] or receipt["reason"]) if receipt else None,
            "receipt": receipt["path"] if receipt else None,
            "text": entry["text"],
        })
    return out


# --- the page ---------------------------------------------------------------------

STYLE = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0; background: #f6f5f2; color: #1d1c1a;
       font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
main { max-width: 40rem; margin: 0 auto; padding: 20px 16px 56px; }
h1 { font-size: 1.4rem; margin: 0 0 4px; line-height: 1.25; }
h2 { font-size: 1.05rem; margin: 34px 0 6px; padding-top: 14px; border-top: 1px solid #d9d6cf; }
p { margin: 6px 0; }
.sub { color: #57534a; margin: 0 0 6px; }
.note { color: #57534a; font-size: 0.86rem; margin: 2px 0 12px; }
.card { background: #fff; border: 1px solid #e2ded5; border-radius: 8px;
        padding: 10px 12px; margin: 8px 0; }
.row { display: flex; flex-wrap: wrap; gap: 6px; align-items: baseline; }
.tag { font-size: 0.72rem; letter-spacing: 0.04em; text-transform: uppercase;
       border-radius: 999px; padding: 1px 8px; border: 1px solid currentColor; }
.landed { color: #1c6b3f; } .refused { color: #9a2c2c; } .started { color: #4a5568; }
.killed { color: #6b5b1c; } .undo { color: #6b3f8a; }
code, .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
              font-size: 0.85em; }
.num { font-variant-numeric: tabular-nums; }
.q { border-left: 3px solid #c9a227; padding-left: 10px; margin: 10px 0; }
.where { color: #57534a; font-size: 0.8rem; }
.bar { height: 8px; border-radius: 4px; background: #dcd8cf; overflow: hidden; margin-top: 4px; }
.bar > span { display: block; height: 100%; background: #4a5568; }
.bar > span.wide { background: #8d9bb0; }
table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
th, td { text-align: left; padding: 5px 6px; border-bottom: 1px solid #e2ded5; vertical-align: top; }
th { font-weight: 600; color: #57534a; font-size: 0.78rem; text-transform: uppercase;
     letter-spacing: 0.04em; }
.empty { color: #57534a; font-style: italic; }
footer { margin-top: 34px; padding-top: 14px; border-top: 1px solid #d9d6cf;
         color: #57534a; font-size: 0.84rem; }
"""


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def bar(value: float, largest: float, wide: bool = False) -> str:
    """A bar as an integer percentage: a float width would be a float in the bytes."""
    percent = 0 if largest <= 0 else int(round(100.0 * value / largest))
    return '<div class="bar"><span class="%s" style="width:%d%%"></span></div>' % (
        "wide" if wide else "", max(0, min(100, percent)))


def render(data: dict) -> str:
    out: list[str] = []
    write = out.append
    counts = {}
    for entry in data["board"]:
        key = "undo" if entry["undo"] else entry["kind"]
        counts[key] = counts.get(key, 0) + 1

    write("<!doctype html>")
    write('<html lang="en"><head><meta charset="utf-8">')
    write('<meta name="viewport" content="width=device-width, initial-scale=1">')
    write("<title>How this desk works</title>")
    write("<style>%s</style></head><body><main>" % STYLE)

    write("<h1>How this desk works</h1>")
    write('<p class="sub">Read off <code>%s</code>: its landing receipts, its board, '
          "its packets and the runs under its submissions. Nothing else was looked at, "
          "and nothing here is a grade.</p>" % esc(data["name"]))
    write('<p class="note">%s</p>' % esc(
        "%d board line(s): %s. %d receipt(s). %d packet(s). %d {?} line(s). %d run record(s)."
        % (
            len(data["board"]),
            ", ".join("%d %s" % (counts[k], k) for k in sorted(counts)) or "none",
            len(data["receipts"]),
            len(data["packets"]),
            len(data["questions"]),
            len(data["runs"]),
        )))

    # 1. what they retried
    write("<h2>What they retried</h2>")
    write('<p class="note">A task that was refused and then landed. The refusal is not '
          "a mark against them; it is the only place the record shows a correction.</p>")
    again = retried(data)
    if not again:
        write('<p class="empty">Nothing was refused and then landed.</p>')
    for item in again:
        write('<div class="card">')
        write('<div class="row"><strong>%s</strong></div>' % esc(item["package"]))
        for attempt in item["tries"]:
            score = ("%s/%s" % (attempt["passed"], attempt["total"])) if attempt["passed"] else "no score"
            write('<div class="row"><span class="tag %s">%s</span>'
                  '<span class="num mono">%s</span>'
                  '<span class="where">%s</span></div>'
                  % (esc(attempt["kind"]), esc(attempt["kind"]), esc(score), esc(attempt["text"])))
        write("</div>")

    # 2. what they undid
    write("<h2>What they undid</h2>")
    write('<p class="note">An undo is a landing in reverse, with a receipt of its own. '
          "It costs nothing and leaves the history intact, which is the point of having it.</p>")
    backouts = undone(data)
    if not backouts:
        write('<p class="empty">Nothing was undone.</p>')
    for entry in backouts:
        write('<div class="card"><div class="row">'
              '<span class="tag undo">undo</span><strong>%s</strong></div>'
              '<p class="where">%s</p></div>' % (esc(entry["task"]), esc(entry["text"])))

    # 3. where they wrote {?}
    write("<h2>Where they wrote <code>{?}</code></h2>")
    write('<p class="note">The habit the whole record is built on: one line for each '
          "thing you were not sure of, left where the next reader will find it.</p>")
    if not data["questions"]:
        write('<p class="empty">No {?} line anywhere on this desk.</p>')
    last_file = None
    for item in data["questions"]:
        if item["path"] != last_file:
            write('<p class="where mono">%s</p>' % esc(item["path"]))
            last_file = item["path"]
        write('<div class="q">%s <span class="where">line %d</span></div>'
              % (esc(item["text"]), item["line"]))

    # 4. how long each Tick took them
    write("<h2>How long each Tick took them</h2>")
    write('<p class="note">From the run records they submitted, not from anything this '
          "page ran. Work is what the Calculations in the Tick add up to; latency is the "
          "longest one on its own. Where the two differ, the Tick could have run side by side.</p>")
    if not data["runs"]:
        write('<p class="empty">No run record under any submission.</p>')
    for run in data["runs"]:
        write('<p class="where mono">%s</p>' % esc(run["path"]))
        largest = max([tick["work"] for tick in run["ticks"]] + [0.0])
        write('<table><tr><th>tick</th><th>calculations</th><th>work ms</th><th>latency ms</th></tr>')
        for tick in run["ticks"]:
            write("<tr><td><strong>%s</strong>%s</td><td class=\"mono\">%s</td>"
                  '<td class="num">%.3f</td><td class="num">%.3f</td></tr>'
                  % (esc(tick["name"]), bar(tick["work"], largest),
                     esc(", ".join(tick["calculations"])), tick["work"], tick["latency"]))
        write("</table>")
        write('<p class="note">%s</p>' % esc(
            "%s invocation(s), %s of them served from the cache."
            % (run["invocations"], run["hits"])))

    # 5. what scored what
    write("<h2>What scored what</h2>")
    write('<p class="note">Every score on this desk, and the command that produced it. '
          "A score is information; the exit code is the verdict.</p>")
    scores = scored(data)
    if not scores:
        write('<p class="empty">No verifier on this desk printed a score.</p>')
    else:
        write("<table><tr><th>package</th><th>score</th><th>verdict</th>"
              "<th>verifier, and the receipt it left</th></tr>")
        for item in scores:
            write('<tr><td class="mono">%s</td><td class="num">%d/%d</td>'
                  '<td><span class="tag %s">%s</span></td>'
                  '<td class="mono">%s<br><span class="where">%s</span></td></tr>'
                  % (esc(item["package"]), item["passed"], item["total"],
                     esc(item["kind"]), esc(item["kind"]),
                     esc(item["verifier"] or "-"), esc(item["receipt"] or "no receipt")))
        write("</table>")

    write("<h2>The tasks this desk holds</h2>")
    write("<table><tr><th>task</th><th>state</th><th>intent</th></tr>")
    for packet in data["packets"]:
        write('<tr><td class="mono">%s</td><td>%s</td><td>%s</td></tr>'
              % (esc(packet["task"]), "open" if packet["open"] else "landed", esc(packet["intent"])))
    write("</table>")

    write("<footer>Every line above points at a file on this desk. The page reads no "
          "clock and prints no path from outside the desk, so two runs over the same "
          "desk are the same bytes and a difference is a difference in the record. "
          "A record shows what somebody did, not whether they understood it: identical "
          "digests prove the same computation, not the right answer.</footer>")
    write("</main></html>")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("desk", help="the student's desk repository")
    ns = parser.parse_args(argv)
    if not os.path.isdir(ns.desk):
        print("tutor.py: no such desk: %s" % ns.desk, file=sys.stderr)
        return 2
    sys.stdout.write(render(read_desk(ns.desk)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
