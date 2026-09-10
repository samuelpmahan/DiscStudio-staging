"""Render a retained program as the browser readPql document, or refuse it.

Experiment-local. The grammar is src/core/exec.js:37-49 (`readPql`), reached from
Python only as data: this module writes JSON that node's reader accepts, it never
executes JavaScript. candidates/readpql_check.mjs runs the real reader over the
output.

What the grammar can hold (exec.js:39-46):

    {"PrincipleComponentRender": <nonempty string>,
     "Ticks": [{"name": <nonempty string>,
                "Calculations": [{"call": "fn.<...>",
                                  "with": {name: <nonempty address string>},
                                  "args": {...},
                                  "into": <nonempty string>}]}]}

What it cannot hold, and why `to_pql_document` refuses rather than degrades:

* a `fn:` binding. `with` values are Part addresses; the reader would happily
  accept the *string* "fn:split" (exec.js:45 only checks it is a nonempty
  string) and `invokePql` would then call `pxc.get("fn:split")` and die at run
  time with "slot 'fn:split' not produced yet" (exec.js:15, :56). A retained
  program that silently becomes a document that fails later is worse than one
  that is refused now, so the fn: refusal happens here, in Python.
* an invocation without `into`: exec.js:46 requires a nonempty string, so the
  optional `into` that PCR allows (pcr.py:29, :112-116) has no representation.
* an invocation that publishes several Parts. `into` in a retained program is one
  address, an array of addresses, or null (RECORD.md, Field rules), but the
  grammar has one `into` per Calculation and it must be a nonempty *string*
  (exec.js:46, `text(calculation.into, ...)`); `invokePql` then writes exactly one
  address per Calculation (`pxc.set(calculation.into, output)`, exec.js:58). There
  is no place in the document for the second address and no way for the reader to
  split one result across two, so a multi-produce invocation is refused here,
  naming the invocation and every address it declared, rather than emitted with
  one address chosen and the rest silently dropped.
* an args key shadowing a `with` key: exec.js:45 rejects the document outright.
  retain.to_program refuses the same thing at export, so a program that reached
  this module has already passed that rule; it is re-checked here because a
  document may be built from a hand-written program dict.

Invocation ids have no place in the grammar either. They are dropped, which is
the third reason this shape loses the candidates/ comparison: `fn:` refs are
addressed by id, so a document that drops ids cannot express them even in
principle.
"""

from __future__ import annotations

from typing import Any, Mapping

PX = "px:"
FN = "fn:"


class PqlDocumentError(ValueError):
    """The program cannot be expressed in the readPql grammar (src/core/exec.js:37-49)."""


def _where(tick_name: str, entry: Mapping[str, Any]) -> str:
    return f"{tick_name}.{entry.get('id', '<no id>')}"


def to_pql_document(program: Mapping[str, Any]) -> dict[str, Any]:
    """The readPql document for a px-only, fully-published program. Raises otherwise."""
    if not isinstance(program, Mapping):
        raise PqlDocumentError(f"to_pql_document: expected a program mapping, got {type(program).__name__}")
    name = program.get("name")
    if not isinstance(name, str) or not name:
        raise PqlDocumentError("to_pql_document: program['name'] must be a nonempty string (exec.js:39)")

    ticks: list[dict[str, Any]] = []
    for tick in program.get("ticks", []):
        tick_name = tick.get("name")
        if not isinstance(tick_name, str) or not tick_name:
            raise PqlDocumentError("to_pql_document: every tick needs a nonempty name (exec.js:41)")
        calculations: list[dict[str, Any]] = []
        for entry in tick.get("calculations", []):
            where = _where(tick_name, entry)
            call = entry.get("calculation")
            if not isinstance(call, str) or not call.startswith("fn."):
                raise PqlDocumentError(
                    f"to_pql_document: {where} call '{call}' must be a registered fn. address (exec.js:43)"
                )
            bindings: dict[str, str] = {}
            for input_name, ref in (entry.get("inputs") or {}).items():
                if isinstance(ref, str) and ref.startswith(PX):
                    bindings[input_name] = ref[len(PX):]
                    continue
                raise PqlDocumentError(
                    f"to_pql_document: {where} binds '{input_name}' to '{ref}'; the readPql "
                    f"grammar has only Part addresses in 'with' (exec.js:44-46), so a direct "
                    f"result reference cannot be expressed and is refused rather than written "
                    f"as the literal address '{ref}'"
                )
            into = entry.get("into")
            if isinstance(into, (list, tuple)) and into:
                addresses = list(into)
                raise PqlDocumentError(
                    f"to_pql_document: {where} declares 'into' as an array of "
                    f"addresses {addresses}, so it publishes several Parts from one "
                    f"invocation; exec.js:46 takes one nonempty 'into' string per "
                    f"Calculation and invokePql writes that one address "
                    f"(exec.js:58), so a multi-produce invocation cannot be "
                    f"expressed and is refused rather than written with one of its "
                    f"addresses"
                )
            if not isinstance(into, str) or not into:
                raise PqlDocumentError(
                    f"to_pql_document: {where} has no 'into'; exec.js:46 requires a nonempty "
                    f"string, so an unpublished result cannot be expressed"
                )
            args = dict(entry.get("args") or {})
            shadowed = sorted(set(args) & set(bindings))
            if shadowed:
                raise PqlDocumentError(
                    f"to_pql_document: {where} has args {shadowed} shadowing 'with' key(s) of the "
                    f"same name (exec.js:45)"
                )
            calculations.append({"call": call, "with": bindings, "args": args, "into": into})
        ticks.append({"name": tick_name, "Calculations": calculations})
    return {"PrincipleComponentRender": name, "Ticks": ticks}


def can_render(program: Mapping[str, Any]) -> tuple[bool, str | None]:
    """(True, None) or (False, first refusal message). No exception."""
    try:
        to_pql_document(program)
    except PqlDocumentError as error:
        return False, str(error)
    return True, None
