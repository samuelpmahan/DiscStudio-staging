#!/usr/bin/env python3
"""The walk: one static page that steps through every landing on the board, oldest first.

    python scripts/walk.py [--out walk.html]   build the page (default ./walk.html)
    python scripts/walk.py --list              one line per landing: step, stamp, task, intent
    python scripts/walk.py --text N            one step as plain text, for an agent
    python scripts/walk.py --check             build twice in memory; non-zero on drift or a
                                               landed line with no receipt or no landing commit

Everything is derived from git and the files under pyto/: the board's "## Today" landed lines
give the order, each landing's receipt gives the verdict, the landing commit gives the change.
No clock is read, no absolute path is written, the output is LF only; same tree, same bytes.
Standard library only, apart from this repository's own `pyto` package (`pyto.neat.review`, for
the question loop's answered state -- one parser, one answers directory, read here and by `neat
ask`, never two).
"""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
import textwrap

import pyto.neat.review as neat_review

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # the repository (pyto/ is one level down)
PYTO_DIR = os.path.join(ROOT, "pyto")
sys.path.insert(0, HERE)
from board_page import inline  # noqa: E402  (the board's renderer: same inline markup, same tokens)


def question_status(line: str) -> str:
    """"open", or "answered <digest first 12>" -- the label of one raw `{?}` line, looked up in
    `pyto/experiments/review/answers/` the same way `neat answers` does (`pyto.neat.review.
    answer_for`), so a step and the CLI never disagree about what counts as answered."""
    label, _ = neat_review.split_question_line(line)
    answer = neat_review.answer_for(PYTO_DIR, label)
    if answer is None:
        return "open"
    kind = answer.get("kind", "owner")
    return f"{'answered' if kind == 'owner' else 'default'} {answer['sha256'][:12]}"

DIFF_CAP = 60 * 1024
WIDTH = 100

# The seven concepts, in the owner's register, each with where it lives on the record.
CONCEPTS = [
    ("Part", "an address with a value in the store; everything you can read back is one",
     "pyto/USE.md section 2"),
    ("PxC", "the store: get, set, has, register, call; the one interface every Part is behind",
     "pyto/USE.md section 1"),
    ("Calculation", "fn. is pure, oc. has effects, and effects go through the run's handle",
     "pyto/USE.md section 3"),
    ("PCR and Tick", "a program is Ticks in order; inside a Tick the Calculations are a sequence in "
     "declared order, the Tick boundary is where that sequence becomes inspectable, and a Tick with "
     "no sibling reads may run at once", "pyto/questions.md ChainsInsideATick"),
    ("receipt", "what one Calculation read, wrote and produced; a Part under px.receipt.",
     "pyto/USE.md section 5"),
    ("PQL", "the query over addresses: part, prefix, where, matches, values, addresses, one, "
     "optional, receipts", "pyto/USE.md section 6"),
    ("neat", "a task is a copy that lands only on green with a receipt; undo is a sentence",
     "pyto/scripts/neat.sh"),
]
DEFINITION = {name: text for name, text, _ in CONCEPTS}

# Changed paths -> concepts touched. First match wins per rule; a path may name several concepts.
PATH_RULES = [
    (re.compile(r"^pyto/src/pyto/(core|px)\.py$"), ["PxC", "Part"]),
    (re.compile(r"^pyto/src/pyto/pql\.py$"), ["PQL"]),
    (re.compile(r"^pyto/src/pyto/pcr\.py$"), ["PCR and Tick", "Calculation"]),
    (re.compile(r"^pyto/src/pyto/effects\.py$"), ["Calculation"]),
    (re.compile(r"^pyto/src/pyto/materialize\.py$|^pyto/viewer/"), ["receipt", "record"]),
    (re.compile(r"^pyto/scripts/(neat|land)\.sh$|^pyto/experiments/classroom/"), ["neat"]),
    (re.compile(r"^src/"), ["the studio"]),
    (re.compile(r"^pyto/experiments/"), ["experiments"]),
    (re.compile(r"^pyto/tests/|^tests/"), ["tests"]),
    (re.compile(r"^pyto/src/pyto/"), ["PxC"]),
    (re.compile(r"^pyto/scripts/|^scripts/|^\.github/"), ["neat"]),
]
OTHER = {
    "record": "the run written down: every receipt of a run, replayable without the program",
    "the studio": "DiscStudio, the JavaScript side that runs the same Ticks in a browser",
    "experiments": "a run kept under pyto/experiments with its own evidence and report",
    "tests": "the executable spec: a test names the paragraph that would lie",
    "docs": "prose on the record: the board, the questions, the hand-offs",
}

LANDED = re.compile(r"^- (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \*\*landed\*\* `([^`]+)`(?: score (\S+))?: (.*)$")
TAIL = re.compile(r"\s*\((\d+) files since ([0-9a-f]+), suites green, receipt (\S+)\)\s*$")
# The record itself sometimes carries a machine's absolute path (a refusal line, a check_all.txt);
# the page carries none, so the same tree on any machine gives the same bytes.
ABSOLUTE = re.compile(r"(?<![\w/.])(?:/(?:home|Users|root|tmp|private|var|mnt|opt)/|[A-Za-z]:[/\\])[^\s\"'<>)\]&#;,]*")  # stops before an html entity, so an escaped quote after a path survives
CUT_PATH = "(absolute path cut)"

OWNER = re.compile(r"(?:the )?owner[^'\"\n]{0,40}?[:,]\s*(['\"])(.+?)\1(?=[\s.,;:)]|$)", re.I)


def run_git(*args: str) -> str:
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def read(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


# ----------------------------------------------------------------------------- the record

def board_landings() -> list[dict]:
    """The board's landed lines, oldest first."""
    md = read("pyto/BOARD.md")
    today = md.split("\n## Today", 1)[1] if "\n## Today" in md else md
    out = []
    for line in today.splitlines():
        m = LANDED.match(line)
        if not m:
            continue
        stamp, package, score, text = m.groups()
        t = TAIL.search(text)
        intent = TAIL.sub("", text) if t else text
        out.append({"stamp": stamp, "package": package, "score": score, "intent": intent,
                    "files": int(t.group(1)) if t else None, "since": t.group(2) if t else "",
                    "receipt_id": t.group(3) if t else ""})
    out.reverse()
    return out


def landing_commits() -> dict[str, dict]:
    """One pass over every landing commit: subject, body, numstat and patch against the first parent.
    Keyed by receipt id (from the commit body) and by package (the newest wins)."""
    sep = "\x00\x00WALK\x00\x00"
    # Every landing commit reachable from here, whichever parent it sits behind (a copy that merged
    # MAIN reaches MAIN's landings through the merge's second parent), each diffed against its own
    # first parent, which is what the landing changed.
    shas = [line for line in run_git("log", "--format=%H", "--grep=^land(").split("\n") if line]
    raw = run_git("show", "--first-parent", "-m", "--numstat", "-p", "--no-color",
                  "--format=%x00%x00WALK%x00%x00%H%x00%s%x00%b%x00", *shas) if shas else ""
    found: dict[str, dict] = {}
    for chunk in raw.split(sep)[1:]:
        sha, subject, body, rest = chunk.split("\x00", 3)
        numstat, patch_lines, in_patch = [], [], False
        for line in rest.split("\n"):
            if in_patch:
                patch_lines.append(line)
                continue
            if line.startswith("diff --git "):
                in_patch = True
                patch_lines.append(line)
                continue
            parts = line.split("\t")
            if len(parts) == 3 and line.strip():
                numstat.append((parts[2], parts[0], parts[1]))
        pm = re.match(r"^land\(([^)]+)\): (.*)$", subject, re.S)
        package = pm.group(1) if pm else ""
        rm = re.search(r"Landing receipt: pyto/experiments/landings/(?:failed/)?([^/\s]+)", body)
        entry = {"sha": sha, "package": package, "subject": pm.group(2) if pm else subject,
                 "numstat": sorted(numstat), "patch": "\n".join(patch_lines).rstrip("\n")}
        if rm:
            found.setdefault("receipt:" + rm.group(1), entry)
        found.setdefault("package:" + package, entry)  # log is newest first: first seen is newest
    return found


def load_receipt(rid: str) -> dict | None:
    for rel in (f"pyto/experiments/landings/{rid}/receipt.json",
                f"pyto/experiments/landings/failed/{rid}.json"):
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return None


def packet_of(package: str) -> tuple[str, list[str], bool]:
    """(intent line, {?} lines, hand-off present) for task-N packages; empty otherwise."""
    m = re.match(r"^task-(\d+)$", package)
    if not m:
        return "", [], False
    d = os.path.join(ROOT, "pyto", "experiments", "tasks", m.group(1))
    p = os.path.join(d, "packet.md")
    if not os.path.isfile(p):
        return "", [], False
    text = read(f"pyto/experiments/tasks/{m.group(1)}/packet.md")
    intent = ""
    for line in text.splitlines():
        if line.startswith("Intent: "):
            intent = line[len("Intent: "):]
            break
    unsure = text.split("\n## Uncertain", 1)[1] if "\n## Uncertain" in text else ""
    qs = [line for line in unsure.splitlines() if line.startswith("{?}")]
    return intent, qs, os.path.isfile(os.path.join(d, "HANDOFF.md"))


def owner_words(*texts: str) -> list[str]:
    seen, out = set(), []
    for t in texts:
        for m in OWNER.finditer(t or ""):
            q = m.group(2).strip()
            if q and q not in seen:
                seen.add(q)
                out.append(q)
    return out


def concepts_of(paths: list[str]) -> list[str]:
    hit: list[str] = []
    for path in paths:
        names = None
        for rule, cs in PATH_RULES:
            if rule.search(path):
                names = cs
                break
        for c in names or ["docs"]:
            if c not in hit:
                hit.append(c)
    order = [c for c, _, _ in CONCEPTS] + list(OTHER)
    return sorted(hit, key=order.index)


def build_steps() -> tuple[list[dict], list[str]]:
    """Every landing on the board as a step, plus the problems --check reports."""
    commits = landing_commits()
    steps, problems = [], []
    for row in board_landings():
        rid, package = row["receipt_id"], row["package"]
        receipt = load_receipt(rid) if rid else None
        commit = commits.get("receipt:" + rid) or commits.get("package:" + package)
        if receipt is None:
            problems.append(f"no receipt for landed {package} ({rid or 'no receipt id on the line'})")
        if commit is None:
            problems.append(f"no landing commit for landed {package} (receipt {rid})")
        packet_intent, qs, handoff = packet_of(package)
        numstat = commit["numstat"] if commit else []
        counts = ((receipt or {}).get("check_all") or {}).get("counts") or {}
        steps.append({
            **row, "receipt": receipt, "commit": commit,
            "intent_full": commit["subject"] if commit else row["intent"],
            "owner": owner_words(row["intent"], commit["subject"] if commit else "", packet_intent),
            "result": (receipt or {}).get("result", "no receipt"),
            "rscore": (receipt or {}).get("score"),
            "tests": sum(v for v in counts.values() if isinstance(v, int)),
            "base": ((receipt or {}).get("base_sha") or "")[:7],
            "sha": (commit or {}).get("sha", ""),
            "numstat": numstat,
            "concepts": concepts_of([p for p, _, _ in numstat]),
            "questions": qs, "handoff": handoff,
        })
    for i, s in enumerate(steps, 1):
        s["n"] = i
    return steps, problems


# ----------------------------------------------------------------------------- the page

CSS = """
:root{--paper:#F5F7F4;--ink:#1B2630;--muted:#5B6A75;--rule:#D3DADD;--panel:#ECEFEC;--landed:#2F6F4E;--landed-bg:#E4F0E8;--refused:#B8352A;--refused-bg:#F8E8E5;--started:#2C5F8A;--started-bg:#E3ECF4;--note:#6B6350;--note-bg:#EFEBE1}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#141A1F;--ink:#E6EAEC;--muted:#9AA7B0;--rule:#2B353D;--panel:#1C242B;--landed:#6FBF8F;--landed-bg:#1B2E25;--refused:#E0604F;--refused-bg:#33211F;--started:#7FB3E0;--started-bg:#1C2B38;--note:#C8BFA6;--note-bg:#2A2722}}
:root[data-theme="dark"]{--paper:#141A1F;--ink:#E6EAEC;--muted:#9AA7B0;--rule:#2B353D;--panel:#1C242B;--landed:#6FBF8F;--landed-bg:#1B2E25;--refused:#E0604F;--refused-bg:#33211F;--started:#7FB3E0;--started-bg:#1C2B38;--note:#C8BFA6;--note-bg:#2A2722}
body{background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.5;padding:0 18px;padding-block:20px 64px}
main{max-width:84ch;margin:0 auto}
h1{font-size:26px;margin:0 0 6px}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
.pin{position:sticky;top:0;background:var(--paper);border-bottom:1px solid var(--rule);padding:8px 0 6px;z-index:2}
.pin dl{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;margin:0;font-size:13px}
.pin dt{font-family:"IBM Plex Mono",ui-monospace,monospace;font-weight:500;white-space:nowrap}
.pin dd{margin:0;color:var(--muted)}
.pin dd .where{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px}
.pin summary{cursor:pointer;font-size:13px;color:var(--muted)}
#progress{position:fixed;top:8px;right:14px;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--muted);background:var(--panel);border:1px solid var(--rule);padding:2px 8px;z-index:3}
section.step{border-top:1px solid var(--rule);padding-top:12px;margin-top:18px}
body.js section.step{display:none}
body.js section.step.on{display:block}
.nav{display:flex;gap:8px;align-items:center;margin:6px 0}
.nav button{font:inherit;font-size:13px;padding:3px 10px;border:1px solid var(--rule);background:var(--panel);color:var(--ink);cursor:pointer}
.nav .where{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--muted);margin-left:auto}
.stamp{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--muted)}
.task{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;padding:1px 7px;border:1px solid var(--landed);color:var(--landed);background:var(--landed-bg)}
.task.failed{border-color:var(--refused);color:var(--refused);background:var(--refused-bg)}
h2{font-size:18px;margin:8px 0 6px;line-height:1.35}
.intent{margin:0 0 10px}
blockquote{margin:8px 0;padding:6px 12px;border-left:3px solid var(--note);background:var(--note-bg);color:var(--ink);font-size:15px}
.receipt{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:13px;color:var(--muted);margin:6px 0}
ul{margin:0 0 12px;padding-left:20px}
ul.concepts li b{font-family:"IBM Plex Mono",ui-monospace,monospace;font-weight:500}
.scroll{overflow-x:auto;max-width:100%}
table{border-collapse:collapse;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:13px;margin:6px 0 10px}
td{padding:1px 10px 1px 0;white-space:nowrap;vertical-align:top}
td.n{text-align:right;color:var(--muted)}
td.add{color:var(--landed)}td.del{color:var(--refused)}
code{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:.92em;background:var(--panel);padding:1px 4px}
pre{background:var(--panel);border:1px solid var(--rule);padding:12px 14px;overflow-x:auto;font-size:12px;line-height:1.4;margin:10px 0 14px}
pre code{background:none;padding:0}
details.diff summary{cursor:pointer;color:var(--muted);font-size:14px}
.q{font-family:"IBM Plex Mono",ui-monospace,monospace;color:var(--refused);font-weight:500}
.undo{margin:10px 0 0;font-weight:600}
footer{margin-top:30px;font-size:13px;color:var(--muted);border-top:1px solid var(--rule);padding-top:10px}
"""

JS = """
(function(){
  var steps=Array.prototype.slice.call(document.querySelectorAll('section.step'));
  if(!steps.length)return;
  document.body.classList.add('js');
  var cur=0,prog=document.getElementById('progress');
  function show(i,push){
    if(i<0)i=0;if(i>=steps.length)i=steps.length-1;
    steps.forEach(function(s,k){s.classList.toggle('on',k===i);});
    cur=i;prog.textContent=(i+1)+' / '+steps.length;
    var h='#step-'+(i+1);
    if(push&&location.hash!==h){history.replaceState(null,'',h);}
    window.scrollTo(0,0);
  }
  function fromHash(){var m=/^#step-(\\d+)$/.exec(location.hash);show(m?parseInt(m[1],10)-1:0,false);}
  window.addEventListener('hashchange',fromHash);
  document.addEventListener('keydown',function(e){
    if(e.target&&/^(INPUT|TEXTAREA)$/.test(e.target.tagName))return;
    if(e.key==='ArrowRight'||e.key==='j'){show(cur+1,true);e.preventDefault();}
    else if(e.key==='ArrowLeft'||e.key==='k'){show(cur-1,true);e.preventDefault();}
  });
  document.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('button[data-go]');
    if(!b)return;show(cur+parseInt(b.getAttribute('data-go'),10),true);
  });
  fromHash();
})();
"""


def strip_html() -> str:
    rows = "".join(f"<dt>{html.escape(n)}</dt><dd>{html.escape(d)} <span class=\"where\">({html.escape(w)})</span></dd>"
                   for n, d, w in CONCEPTS)
    return ('<div class="pin"><details open><summary>The seven words, pinned</summary>'
            f'<dl>{rows}</dl></details></div>')


def receipt_line(s: dict) -> str:
    bits = [s["result"]]
    if s["rscore"] not in (None, ""):
        bits.append(f"score {s['rscore']}")
    elif s["score"]:
        bits.append(f"score {s['score']}")
    bits.append(f"{s['tests']} tests across the suites")
    bits.append(f"base {s['base'] or '?'} to landing {s['sha'][:7] or '?'}")
    gate = (s.get("receipt") or {}).get("gate") or {}
    if gate.get("allowed") and gate.get("trusted"):
        bits.append(gate.get("reason", "approved"))
    elif gate.get("stub_allowed"):
        bits.append("stub gate, never trusted")
    else:
        bits.append("unapproved")
    bits.append(f"receipt {s['receipt_id'] or '?'}")
    return "; ".join(bits)


def nav(i: int, total: int) -> str:
    return (f'<div class="nav"><button data-go="-1" type="button">prev</button>'
            f'<button data-go="1" type="button">next</button>'
            f'<span class="where">{i} of {total}</span></div>')


def step_html(s: dict, total: int) -> str:
    n = s["n"]
    out = [f'<section class="step" id="step-{n}">', nav(n, total),
           f'<p class="eyebrow">step {n} of {total}</p>',
           f'<p><span class="stamp">{html.escape(s["stamp"])}</span> '
           f'<span class="task{" failed" if s["result"] != "verified" else ""}">{html.escape(s["package"])}</span></p>',
           f'<h2>{inline(s["intent_full"])}</h2>']
    if s["intent_full"] != s["intent"]:
        out.append(f'<p class="intent">On the board: {inline(s["intent"])}</p>')
    for q in s["owner"]:
        out.append(f'<blockquote>The owner: &ldquo;{html.escape(q)}&rdquo;</blockquote>')
    out.append(f'<p class="receipt">{html.escape(receipt_line(s))}</p>')
    out.append('<p class="eyebrow">concepts touched</p><ul class="concepts">')
    for c in s["concepts"]:
        out.append(f'<li><b>{html.escape(c)}</b>: {html.escape(DEFINITION.get(c) or OTHER[c])}</li>')
    if not s["concepts"]:
        out.append("<li>nothing on the record changed</li>")
    out.append("</ul>")
    out.append(f'<p class="eyebrow">files changed ({len(s["numstat"])})</p><div class="scroll"><table>')
    for path, a, d in s["numstat"]:
        out.append(f'<tr><td>{html.escape(path)}</td><td class="n add">+{html.escape(a)}</td>'
                   f'<td class="n del">-{html.escape(d)}</td></tr>')
    out.append("</table></div>")
    if s["commit"]:
        patch = s["commit"]["patch"]
        cut = ""
        if len(patch.encode("utf-8")) > DIFF_CAP:
            patch = patch.encode("utf-8")[:DIFF_CAP].decode("utf-8", "ignore")
            cut = f"\ndiff cut here; git show {s['sha']}"
        out.append(f'<details class="diff"><summary>the whole diff of this landing ({s["sha"][:7]})</summary>'
                   f'<pre><code>{html.escape(patch)}{html.escape(cut)}</code></pre></details>')
    if s["questions"]:
        out.append('<p class="eyebrow">the packet left open</p><ul>')
        out.extend(f"<li>{inline(q)} — {html.escape(question_status(q))}</li>" for q in s["questions"])
        out.append("</ul>")
    if s["handoff"]:
        m = re.match(r"^task-(\d+)$", s["package"])
        out.append(f'<p class="stamp">hand-off: pyto/experiments/tasks/{m.group(1)}/HANDOFF.md</p>')
    m = re.match(r"^task-(\d+)$", s["package"])
    undo = f"undo task {m.group(1)}" if m else f"undo {s['package']}"
    out.append(f'<p class="undo">To undo this one, say: {html.escape(undo)}</p>')
    out.append(nav(n, total))
    out.append("</section>")
    return "\n".join(out)


def build_page(steps: list[dict]) -> str:
    total = len(steps)
    body = "\n".join(step_html(s, total) for s in steps)
    page = (f"<title>The walk</title>\n<style>{CSS}</style>\n"
            f'<div id="progress">1 / {total}</div>\n<main>\n<h1>The walk</h1>\n'
            f'<p class="eyebrow">{total} landings on pyto/BOARD.md, oldest first; arrows or j/k step, '
            f'#step-N is a link to one</p>\n{strip_html()}\n{body}\n'
            f'<footer>Built by pyto/scripts/walk.py from the board, the receipts and the landing commits; '
            f'the same tree gives the same bytes.</footer>\n</main>\n<script>{JS}</script>\n')
    return ABSOLUTE.sub(CUT_PATH, page.replace("\r", ""))


# ----------------------------------------------------------------------------- text and index

def wrap(text: str, indent: str = "  ") -> str:
    return textwrap.fill(text, WIDTH, initial_indent=indent, subsequent_indent=indent,
                         break_long_words=False, break_on_hyphens=False)


def step_text(s: dict, total: int) -> str:
    n = s["n"]
    out = [f"step {n} of {total}: {s['stamp']} {s['package']}", wrap(s["intent_full"], "  ")]
    if s["intent_full"] != s["intent"]:
        out.append(wrap("on the board: " + s["intent"], "  "))
    for q in s["owner"]:
        out.append(wrap(f'the owner: "{q}"', "  > "))
    out.append(wrap("receipt: " + receipt_line(s), "").replace("\n", "\n  "))
    out.append("concepts touched:")
    for c in s["concepts"]:
        out.append(wrap(f"{c}: {DEFINITION.get(c) or OTHER[c]}", "  "))
    if not s["concepts"]:
        out.append("  nothing on the record changed")
    out.append(f"files changed ({len(s['numstat'])}):")
    for path, a, d in s["numstat"]:
        out.append(f"  +{a:<6} -{d:<6} {path}")
    if s["sha"]:
        out.append(f"diff: git show {s['sha']}")
    if s["questions"]:
        out.append("the packet left open:")
        out.extend(wrap(f"{q} — {question_status(q)}", "  ") for q in s["questions"])
    if s["handoff"]:
        out.append(f"hand-off: pyto/experiments/tasks/{s['package'].split('-', 1)[1]}/HANDOFF.md")
    m = re.match(r"^task-(\d+)$", s["package"])
    out.append(f"To undo this one, say: {'undo task ' + m.group(1) if m else 'undo ' + s['package']}")
    out.append(f"next: python scripts/walk.py --text {n + 1}")
    return ABSOLUTE.sub(CUT_PATH, "\n".join(out)) + "\n"


def index_text(steps: list[dict]) -> str:
    return "".join(f"{s['n']:>3}  {s['stamp']}  {s['package']:<18} {s['intent'][:100]}\n" for s in steps)


def main(argv: list[str]) -> int:
    if "--check" in argv:
        steps, problems = build_steps()
        one = build_page(steps)
        again = build_page(build_steps()[0])
        for p in problems:
            print("walk: " + p)
        if one != again:
            print("walk: two builds differ")
        if "\r" in one:
            print("walk: a CR byte in the page")
        print(f"walk: {len(steps)} steps, {len(one)} bytes, {'ok' if not problems and one == again else 'drift'}")
        return 0 if not problems and one == again and "\r" not in one else 1
    if "--list" in argv:
        steps, _ = build_steps()
        sys.stdout.write(index_text(steps))
        return 0
    if "--text" in argv:
        k = argv.index("--text")
        try:
            n = int(argv[k + 1])
        except (IndexError, ValueError):
            print("walk: --text needs a step number", file=sys.stderr)
            return 2
        steps, _ = build_steps()
        if not 1 <= n <= len(steps):
            print(f"walk: no step {n}; the walk has {len(steps)}", file=sys.stderr)
            return 1
        sys.stdout.write(step_text(steps[n - 1], len(steps)))
        return 0
    out = "walk.html"
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    steps, problems = build_steps()
    page = build_page(steps)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    for p in problems:
        print("walk: " + p, file=sys.stderr)
    print(f"walk: {len(steps)} steps -> {out} ({len(page.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
