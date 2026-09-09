#!/usr/bin/env python3
"""Lint SVG files for tournament hygiene.

    lint_svg.py file1.svg file2.svg ...

Checks, per file:
  - well-formed XML
  - root element is <svg> with an xmlns
  - a viewBox attribute is present
  - no href / xlink:href pointing at anything external or a data: URI
    (in-document fragment refs like "#disc" are fine)
  - no <image> elements
  - no @font-face or url(...) in any <style> text or style attribute
  - file size <= 64KB

Exits non-zero and prints every failure (grouped by file) if any file fails
any check; exits 0 and prints one "ok" line per file otherwise.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_BYTES = 64 * 1024
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

_URL_FN_RE = re.compile(r"url\s*\(", re.IGNORECASE)
_FONT_FACE_RE = re.compile(r"@font-face", re.IGNORECASE)


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def lint_bytes(data: bytes, name: str) -> list[str]:
    failures: list[str] = []

    if len(data) > MAX_BYTES:
        failures.append(f"size {len(data)}B exceeds {MAX_BYTES}B cap")

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return failures + [f"not valid UTF-8: {exc}"]

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return failures + [f"not well-formed XML: {exc}"]

    if _local(root.tag) != "svg":
        failures.append(f"root element is <{_local(root.tag)}>, not <svg>")

    if root.tag.startswith("{"):
        ns = root.tag[1:].split("}", 1)[0]
        if ns != SVG_NS:
            failures.append(f"root xmlns is {ns!r}, expected {SVG_NS!r}")
    elif "xmlns" not in text.split(">", 1)[0] and 'xmlns="' + SVG_NS not in text:
        failures.append("root <svg> is missing an xmlns declaration")

    if "viewBox" not in root.attrib:
        failures.append("root <svg> is missing a viewBox attribute")

    for elem in root.iter():
        if _local(elem.tag) == "image":
            failures.append("contains a forbidden <image> element")
        for attr_name, attr_value in elem.attrib.items():
            local_attr = _local(attr_name)
            if local_attr not in ("href",) and not attr_name.endswith("}href"):
                continue
            if attr_value.startswith("#"):
                continue
            failures.append(f"forbidden external/data href on <{_local(elem.tag)}>: {attr_value[:60]!r}")

    if _FONT_FACE_RE.search(text):
        failures.append("contains @font-face")
    for match in _URL_FN_RE.finditer(text):
        # allow url(#fragment) (local paint-server / clip references); forbid anything else
        tail = text[match.end():match.end() + 40].lstrip()
        if not tail.startswith("#") and not tail.startswith("'#") and not tail.startswith('"#'):
            failures.append(f"forbidden url(...) reference near byte {match.start()}")

    return failures


def main() -> None:
    p = argparse.ArgumentParser(description="Lint SVG files for tournament hygiene")
    p.add_argument("files", nargs="+", type=Path)
    args = p.parse_args()

    any_failed = False
    for path in args.files:
        try:
            data = path.read_bytes()
        except OSError as exc:
            print(f"{path}: ERROR could not read file: {exc}")
            any_failed = True
            continue
        failures = lint_bytes(data, str(path))
        if failures:
            any_failed = True
            print(f"{path}: FAIL")
            for failure in failures:
                print(f"  - {failure}")
        else:
            print(f"{path}: ok")

    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
