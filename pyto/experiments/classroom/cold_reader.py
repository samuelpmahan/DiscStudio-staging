"""The mechanical half of the cold read.

    python cold_reader.py <hand-off page> <the reader's answer>

The cold read is the real grade of the students assignment: a person or an agent
who has seen only the hand-off page -- never the code, never the record -- says in
plain words what the program does. Whether that answer is *right* is not something
a script can settle, and this file does not pretend otherwise.

What a script can settle is whether the answer accounts for the page at all. So
this is the same rule as `grade.py` check 4, turned around and pointed at the
reader instead of the writer:

  check 4  the hand-off must name every Tick in the record and every file the
           homework is made of;
  here     the answer must name every Tick the hand-off names and every file the
           hand-off names.

An answer that skips a step of the program has not read the page, whatever else
it says. That is the whole claim. Prints

    cold reader: N of M named

and exits 0 when N == M, 1 otherwise, naming what was left out.

The caveat is the same one the assignment is built around: naming every step
proves the reader covered the page, not that they understood it. A grade still
needs a teacher.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

# The hand-off's Tick list, by the same rule grade.py reads it (grade.py:
# `tick_list_lines`): a bullet is a line that starts at column zero with "- " or
# "* " under the "One line per Tick" heading, and the section runs from that
# heading to the next heading of any level.
TICK_SECTION = "One line per Tick"

# A backticked token is a file name when it looks like one: path characters and a
# short extension, nothing else. This is what keeps `name,score` (a CSV header the
# students page quotes) and `{?}` out of the file list while keeping
# `evidence/run-1/record.json` in it.
FILE_TOKEN = re.compile(r"^[A-Za-z0-9._/-]+\.[A-Za-z0-9]{1,6}$")


def tick_list_lines(handoff_text: str) -> list[str]:
    """The bullets under the hand-off's Tick heading, text only."""
    bullets: list[str] = []
    inside = False
    for line in handoff_text.splitlines():
        if line.startswith("#"):
            inside = TICK_SECTION.lower() in line.lower()
            continue
        if inside and line.startswith(("- ", "* ")):
            bullets.append(line[2:].strip())
    return bullets


def tick_names(handoff_text: str) -> list[str]:
    """The name each Tick bullet opens with, in the page's own order.

    Three spellings, the same three `grade.py:names_tick` accepts from the other
    side: `**Name**` followed by anything, `Name:`, and `Name ` -- plus a bullet
    that is the bare name. Anything else contributes no name, because a bullet
    that does not open with a name is not that Tick's line.
    """
    names: list[str] = []
    for bullet in tick_list_lines(handoff_text):
        bold = re.match(r"^\*\*([^*]+)\*\*", bullet)
        if bold:
            name = bold.group(1).strip()
        else:
            colon = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):", bullet)
            if colon:
                name = colon.group(1)
            else:
                word = bullet.split(" ", 1)[0].strip()
                name = word.strip(".,;:*_`")
        if name and name not in names:
            names.append(name)
    return names


def file_names(handoff_text: str) -> list[str]:
    """Every backticked token on the page that is spelled like a file, sorted."""
    found = []
    for token in re.findall(r"`([^`\n]+)`", handoff_text):
        token = token.strip()
        if FILE_TOKEN.match(token) and token not in found:
            found.append(token)
    return sorted(found)


def names_it(answer: str, name: str, fold_case: bool) -> bool:
    """Does the answer name this thing?

    Substring, exactly as grade.py's file half is a substring search of the
    hand-off: there is no line to look for in a reader's paragraph. Tick names are
    folded to lower case first, because a reader writing prose says "the parse
    step" and means Parse; file names are not, because a file name is a token the
    reader is copying, not a word they are inflecting.
    """
    if fold_case:
        return name.lower() in answer.lower()
    return name in answer


def read(handoff_path: str, answer_path: str) -> tuple[int, list[str]]:
    """The cold read as (exit code, report lines)."""
    with open(handoff_path, encoding="utf-8") as handle:
        handoff_text = handle.read()
    with open(answer_path, encoding="utf-8") as handle:
        answer = handle.read()

    ticks = tick_names(handoff_text)
    files = file_names(handoff_text)
    missing_ticks = [name for name in ticks if not names_it(answer, name, True)]
    missing_files = [name for name in files if not names_it(answer, name, False)]

    named = (len(ticks) - len(missing_ticks)) + (len(files) - len(missing_files))
    total = len(ticks) + len(files)
    lines = [
        "cold reader: %s read against %s"
        % (os.path.basename(handoff_path), os.path.basename(answer_path)),
        "  ticks: %d of %d (%s)" % (len(ticks) - len(missing_ticks), len(ticks), ", ".join(ticks) or "none"),
        "  files: %d of %d" % (len(files) - len(missing_files), len(files)),
    ]
    for name in missing_ticks:
        lines.append("  the answer never names the Tick %r" % name)
    for name in missing_files:
        lines.append("  the answer never names the file %r" % name)
    lines.append("cold reader: %d of %d named" % (named, total))
    if named != total:
        lines.append(
            "the answer does not account for the whole page; naming every step and "
            "file is the floor, not the grade."
        )
    return (0 if named == total else 1), lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("handoff", help="the hand-off page the reader was given")
    parser.add_argument("answer", help="what the reader wrote, plain text")
    ns = parser.parse_args(argv)
    code, lines = read(ns.handoff, ns.answer)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
