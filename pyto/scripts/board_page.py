#!/usr/bin/env python3
"""Render pyto/BOARD.md as one HTML page the owner can read on a phone.

    python3 board_page.py [BOARD.md] [--open "<neat list output>"] > board.html

No dependencies. Headings, paragraphs, bullet lists, fenced code, inline code and bold are
rendered; a "## Today" bullet of the form `- YYYY-MM-DD HH:MM **kind** `task-N`: text` becomes a
timeline row with its stamp, kind and task. Everything else is passed through as prose.
"""
from __future__ import annotations

import html
import re
import sys
from datetime import datetime, timezone

STAMP = re.compile(r"^- (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) (.*)$")
KIND = re.compile(r"^\*\*([^*]+)\*\*\s*(.*)$")
TASK = re.compile(r"^`([^`]+)`:\s*(.*)$", re.S)


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\{\?\}", '<span class="q">{?}</span>', text)
    return text


def today_row(line: str) -> str | None:
    m = STAMP.match(line)
    if not m:
        return None
    date, time, rest = m.groups()
    kind, task, text = "note", "", rest
    k = KIND.match(rest)
    if k:
        kind, rest2 = k.group(1).strip().lower(), k.group(2)
        t = TASK.match(rest2)
        if t:
            task, text = t.group(1), t.group(2)
        else:
            text = rest2.lstrip(": ")
    elif rest.startswith("Owner"):
        kind = "owner"
    cls = re.sub(r"[^a-z]+", "-", kind)
    return (f'<li class="row k-{cls}"><span class="stamp">{date} {time}</span>'
            f'<span class="kind">{html.escape(kind)}</span>'
            + (f'<span class="task">{html.escape(task)}</span>' if task else "")
            + f'<span class="text">{inline(text)}</span></li>')


def render(md: str) -> tuple[str, dict]:
    out, stats = [], {"landed": 0, "refused": 0, "started": 0, "last": ""}
    lines = md.splitlines()
    i, in_code, in_list, in_today, section_open = 0, False, False, False, False
    title = "The Board"

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            close_list()
            if in_code:
                out.append("</code></pre>")
            else:
                out.append("<pre><code>")
            in_code = not in_code
            i += 1
            continue
        if in_code:
            out.append(html.escape(line))
            i += 1
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            i += 1
            continue
        if line.startswith("## ") or line.startswith("### "):
            close_list()
            if section_open:
                out.append("</section>")
            name = line.lstrip("#").strip()
            in_today = name.lower().startswith("today")
            level = "h2" if line.startswith("## ") else "h3"
            sid = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            open_attr = " open" if in_today or name.lower().startswith("the test") else ""
            out.append(f'<section id="{sid}"><details{open_attr}><summary><{level}>{inline(name)}</{level}></summary>')
            section_open = True
            i += 1
            continue
        if line.startswith("- "):
            if not in_list:
                out.append('<ul class="today">' if in_today else "<ul>")
                in_list = True
            row = today_row(line) if in_today else None
            if row:
                out.append(row)
                m = STAMP.match(line)
                k = KIND.match(m.group(3)) if m else None
                if k:
                    kind = k.group(1).strip().lower()
                    if kind in stats:
                        stats[kind] += 1
                    if kind == "landed" and not stats["last"]:
                        stats["last"] = f"{m.group(1)} {m.group(2)}"
            else:
                # continuation lines belong to the bullet until a blank or another bullet
                text = line[2:]
                j = i + 1
                while j < len(lines) and lines[j].startswith("  ") and not lines[j].startswith("- "):
                    text += " " + lines[j].strip()
                    j += 1
                out.append(f"<li>{inline(text)}</li>")
                i = j
                continue
            i += 1
            continue
        if not line.strip():
            close_list()
            i += 1
            continue
        # paragraph: gather until blank / structural line
        para = [line.strip()]
        j = i + 1
        while j < len(lines) and lines[j].strip() and not lines[j].startswith(("- ", "#", "```")):
            para.append(lines[j].strip())
            j += 1
        close_list()
        out.append(f"<p>{inline(' '.join(para))}</p>")
        i = j
    close_list()
    if section_open:
        out.append("</details></section>")
    # every section needs its details closed: sections were opened with <details>; close the previous ones
    body = "\n".join(out).replace("</section>", "</details></section>")
    body = body.replace("</details></details></section>", "</details></section>")
    return body, {**stats, "title": title}


CSS = """
:root{--paper:#F5F7F4;--ink:#1B2630;--muted:#5B6A75;--rule:#D3DADD;--panel:#ECEFEC;--landed:#2F6F4E;--landed-bg:#E4F0E8;--refused:#B8352A;--refused-bg:#F8E8E5;--started:#2C5F8A;--started-bg:#E3ECF4;--note:#6B6350;--note-bg:#EFEBE1}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#141A1F;--ink:#E6EAEC;--muted:#9AA7B0;--rule:#2B353D;--panel:#1C242B;--landed:#6FBF8F;--landed-bg:#1B2E25;--refused:#E0604F;--refused-bg:#33211F;--started:#7FB3E0;--started-bg:#1C2B38;--note:#C8BFA6;--note-bg:#2A2722}}
:root[data-theme="dark"]{--paper:#141A1F;--ink:#E6EAEC;--muted:#9AA7B0;--rule:#2B353D;--panel:#1C242B;--landed:#6FBF8F;--landed-bg:#1B2E25;--refused:#E0604F;--refused-bg:#33211F;--started:#7FB3E0;--started-bg:#1C2B38;--note:#C8BFA6;--note-bg:#2A2722}
body{background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.5;padding:0 18px;padding-block:28px 64px}
main{max-width:76ch;margin:0 auto}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
h1{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:clamp(32px,6vw,44px);line-height:1.05;margin:0 0 14px;text-wrap:balance}
.strip{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 26px}
.strip div{border:1px solid var(--rule);background:var(--panel);padding:8px 12px;font-size:14px;flex:1 1 140px}
.strip .k{display:block;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.strip .n{font-size:22px;font-variant-numeric:tabular-nums;font-family:"IBM Plex Mono",ui-monospace,monospace}
section{border-top:1px solid var(--rule);padding-top:10px;margin-top:14px}
summary{cursor:pointer;list-style:none;display:flex;align-items:baseline;gap:10px}
summary::before{content:"▸";color:var(--muted);font-size:14px}
details[open]>summary::before{content:"▾"}
summary h2,summary h3{font-family:"Fraunces",Georgia,serif;font-weight:600;margin:6px 0;font-size:22px;line-height:1.2}
summary h3{font-size:18px}
p{margin:0 0 12px}
ul{margin:0 0 12px;padding-left:20px}
li{margin:0 0 6px}
code{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:.92em;background:var(--panel);padding:1px 4px}
pre{background:var(--panel);border:1px solid var(--rule);padding:12px 14px;overflow-x:auto;font-size:13px;line-height:1.45;margin:10px 0 14px}
pre code{background:none;padding:0}
.q{font-family:"IBM Plex Mono",ui-monospace,monospace;color:var(--refused);font-weight:500}
ul.today{list-style:none;padding:0;margin:8px 0 0}
.row{display:grid;grid-template-columns:auto auto 1fr;gap:4px 10px;align-items:baseline;padding:8px 0;border-bottom:1px solid var(--rule);font-size:15px}
.row .stamp{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--muted);white-space:nowrap}
.row .kind{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;padding:1px 7px;border:1px solid var(--note);color:var(--note);background:var(--note-bg);white-space:nowrap}
.row .task{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:13px;grid-column:1/-1;margin-top:-2px}
.row .text{grid-column:1/-1;color:var(--ink)}
.k-landed .kind{color:var(--landed);border-color:var(--landed);background:var(--landed-bg)}
.k-refused .kind,.k-failed .kind{color:var(--refused);border-color:var(--refused);background:var(--refused-bg)}
.k-started .kind,.k-for-codex .kind{color:var(--started);border-color:var(--started);background:var(--started-bg)}
.k-owner .kind{color:var(--ink);border-color:var(--ink);background:var(--panel)}
@media (min-width:640px){.row{grid-template-columns:auto auto auto 1fr}.row .task{grid-column:auto;margin:0}.row .text{grid-column:auto}}
footer{margin-top:30px;font-size:13px;color:var(--muted);border-top:1px solid var(--rule);padding-top:10px}
"""


def main(argv: list[str]) -> int:
    path = "pyto/BOARD.md"
    open_copies = ""
    args = list(argv)
    if "--open" in args:
        k = args.index("--open")
        open_copies = args[k + 1]
        del args[k:k + 2]
    if args:
        path = args[0]
    md = open(path, encoding="utf-8").read()
    body, stats = render(md)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    open_rows = [l for l in open_copies.splitlines() if re.match(r"^\d+\s+open", l)]
    open_html = ""
    if open_rows:
        items = "".join(f"<li><code>{html.escape(l.split()[0])}</code> {inline(' '.join(l.split()[3:]))}</li>" for l in open_rows)
        open_html = f'<section id="open"><details open><summary><h2>Open copies</h2></summary><ul>{items}</ul></details></section>'
    page = f"""<title>{html.escape(stats['title'])}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<main>
<p class="eyebrow">pyto/BOARD.md · rendered {now}</p>
<h1>{inline(stats['title'])}</h1>
<div class="strip">
<div><span class="k">last landing</span>{html.escape(stats['last'] or 'none')}</div>
<div><span class="k">landed</span><span class="n">{stats['landed']}</span></div>
<div><span class="k">refused</span><span class="n">{stats['refused']}</span></div>
<div><span class="k">started</span><span class="n">{stats['started']}</span></div>
<div><span class="k">open copies</span><span class="n">{len(open_rows)}</span></div>
</div>
{open_html}
{body}
<footer>Every line under Today was written by the landing script or a note; nothing here is a claim without a receipt. Sections fold; Today and The test start open.</footer>
</main>
"""
    sys.stdout.write(page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
