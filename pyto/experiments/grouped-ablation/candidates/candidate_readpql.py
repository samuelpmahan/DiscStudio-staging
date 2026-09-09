"""Candidate C (browser readPql-shaped) -- NOT MERGED: the grammar has no fn: and no ids.

Renders the program as the document src/core/exec.js:37-49 reads, via
../pql_document.py, and restores it by synthesising invocation ids (`<tick>.<index>`)
because the grammar has no place for them. Retained here as the candidate that
motivated pql_document.py: the shape is the right *interchange* format for a
px-only program (readpql_check.mjs proves node accepts it) and the wrong
*retention* format, because a retained program must survive a round trip.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Mapping

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import retain  # noqa: E402
from pql_document import PqlDocumentError, to_pql_document  # noqa: E402

NAME = "C. browser readPql-shaped"
SHAPE = "{PrincipleComponentRender, Ticks:[{name, Calculations:[{call, with:{k:address}, args, into}]}]}"


def export(program: Mapping[str, Any]) -> dict[str, Any]:
    return to_pql_document(program)


def synthetic_id(tick_name: str, index: int) -> str:
    return f"{tick_name}.{index}"


def restore(document: Mapping[str, Any], registry: Mapping[str, Any]):
    program = {
        "name": document["PrincipleComponentRender"],
        "ticks": [
            {
                "name": tick["name"],
                "calculations": [
                    {
                        "id": synthetic_id(tick["name"], index),
                        "calculation": entry["call"],
                        "inputs": {name: f"px:{address}" for name, address in (entry.get("with") or {}).items()},
                        "args": dict(entry.get("args") or {}),
                        "into": entry.get("into"),
                    }
                    for index, entry in enumerate(tick["Calculations"])
                ],
            }
            for tick in document["Ticks"]
        ],
    }
    return retain.from_program(program, registry)
