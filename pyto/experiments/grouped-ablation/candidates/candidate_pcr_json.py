"""Candidate B (graph.Pcr JSON-shaped) -- NOT MERGED: no importer can exist honestly.

Renders the program through pyto.graph.Pcr and retains `Pcr.to_pcr_dict()`
(graph.py:89-111): {"PrincipleComponentRender", "Ticks":[{"name","Calculations":
[{id, call, with:{k:{kind,ref}}, args, into?}]}]}. Pcr deliberately does not
execute (graph.py:29-31); giving this document a `restore` would present PCR and
Pcr as one round-trip format, which docs/PYTHON-LAB-STEWARDSHIP.md:19 forbids.
`restore` therefore refuses, and refute.py verifies the premise at run time
rather than quoting it.
"""

from __future__ import annotations

from typing import Any, Mapping

from pyto import Pcr
from pyto.graph import PartRef, ValueRef

NAME = "B. graph.Pcr JSON-shaped"
SHAPE = '{PrincipleComponentRender, Ticks:[{name, Calculations:[{id, call, with:{k:{kind,ref}}, args, into?}]}]}'
PX = "px:"
FN = "fn:"


class PcrJsonNotExecutable(NotImplementedError):
    pass


def executes() -> bool:
    """True if graph.Pcr could run a retained document itself. Checked, not assumed."""
    return any(hasattr(Pcr, name) for name in ("run", "invoke", "execute", "from_dict", "from_pcr_dict"))


def export(program: Mapping[str, Any]) -> dict[str, Any]:
    graph = Pcr(program["name"])
    for tick in program["ticks"]:
        for entry in tick["calculations"]:
            inputs: dict[str, Any] = {}
            for name, ref in (entry.get("inputs") or {}).items():
                inputs[name] = PartRef(ref[len(PX):]) if ref.startswith(PX) else ValueRef(ref[len(FN):])
            graph.calc(
                tick["name"],
                entry["calculation"],
                id=entry["id"],
                args=dict(entry.get("args") or {}),
                into=entry.get("into"),
                **inputs,
            )
    return graph.to_pcr_dict()


def restore(document: Mapping[str, Any], registry: Mapping[str, Any]):
    raise PcrJsonNotExecutable(
        "candidate B has no importer: graph.Pcr does not execute (graph.py:29-31) and "
        "PCR and Pcr must not be presented as one round-trip format "
        "(docs/PYTHON-LAB-STEWARDSHIP.md:19). retain.from_program refuses this document "
        "shape for the same reason."
    )
