"""Render a retained program as the browser readPql document, or refuse it.

Experiment-local. The grammar is src/core/exec.js:75-89 (`readPql`), reached from
Python only as data: this module writes JSON that node's reader accepts, it never
executes JavaScript. candidates/readpql_check.mjs runs the real reader over the
output.

What the grammar can hold (exec.js:76-88):

    {"PrincipleComponentRender": <nonempty string>,
     "Ticks": [{"name": <nonempty string>,
                "Calculations": [{"call": "fn.<...>",
                                  "with": {name: <nonempty address string>},
                                  "args": {...},
                                  "into": <nonempty string, or a non-empty
                                           array of distinct addresses>}]}]}

What it cannot hold, and why `to_pql_document` refuses rather than degrades:

* a `fn:` binding. `with` values are Part addresses; the reader would happily
  accept the *string* "fn:split" (exec.js:83 only checks it is a nonempty
  string, and only rejects a misplaced prefix star) and `invokePql` would then
  call `pxc.get("fn:split")` and die at run time with "slot 'fn:split' not
  produced yet" (exec.js:15, :94). A retained program that silently becomes a
  document that fails later is worse than one that is refused now, so the fn:
  refusal happens here, in Python.
* an invocation without `into`: exec.js:84 requires a nonempty string or a
  non-empty array, so the optional `into` that PCR allows (pcr.py:29, :112-116)
  has no representation.
* an args key shadowing a `with` key: exec.js:83 rejects the document outright.
  retain.to_program refuses the same thing at export, so a program that reached
  this module has already passed that rule; it is re-checked here because a
  document may be built from a hand-written program dict.

An invocation that publishes several Parts is no longer on that list. `into` in a
retained program is one address, an array of addresses, or null (RECORD.md, Field
rules), and the grammar now takes the same two shapes: `readPql` reads `into` with
`produces(...)` -- a nonempty string, or a non-empty array of distinct addresses
(exec.js:50-57, :84) -- and `invokePql` publishes one Part per declared address
from one pass, the output being an object keyed by them or an array of the same
length (exec.js:60-70, :98-100). So a multi-produce invocation is emitted here,
carrying every address it declared in declared order; only a malformed array --
empty, or with a repeated or non-string address -- is refused.

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
    """The program cannot be expressed in the readPql grammar (src/core/exec.js:75-89)."""


def _where(tick_name: str, entry: Mapping[str, Any]) -> str:
    return f"{tick_name}.{entry.get('id', '<no id>')}"


def to_pql_document(program: Mapping[str, Any]) -> dict[str, Any]:
    """The readPql document for a px-only, fully-published program. Raises otherwise.

    An invocation may declare one `into` address or several; several are emitted as
    the array the grammar now reads (exec.js:50-57), never collapsed to one.
    """
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
            if isinstance(into, (list, tuple)):
                # Several produces from one pass: the grammar carries every address in
                # declared order (exec.js:50-57), so nothing is chosen and nothing dropped.
                addresses = list(into)
                if not addresses:
                    raise PqlDocumentError(
                        f"to_pql_document: {where} declares an empty 'into'; exec.js:50-52 "
                        f"requires at least one address, so an unpublished result cannot be "
                        f"expressed"
                    )
                seen: set[str] = set()
                for index, address in enumerate(addresses):
                    if not isinstance(address, str) or not address:
                        raise PqlDocumentError(
                            f"to_pql_document: {where} declares 'into'[{index}] as {address!r}; "
                            f"every produce address is a nonempty string (exec.js:53)"
                        )
                    if address in seen:
                        raise PqlDocumentError(
                            f"to_pql_document: {where} declares '{address}' twice in 'into'; one "
                            f"Calculation publishes each address once (exec.js:54)"
                        )
                    seen.add(address)
                into = addresses
            elif not isinstance(into, str) or not into:
                raise PqlDocumentError(
                    f"to_pql_document: {where} has no 'into'; readPql requires a nonempty string "
                    f"or a non-empty array of addresses (exec.js:46 when this refusal was "
                    f"written, `produces` at exec.js:50-57 now that a Calculation may publish "
                    f"several Parts), so an unpublished result cannot be expressed"
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
