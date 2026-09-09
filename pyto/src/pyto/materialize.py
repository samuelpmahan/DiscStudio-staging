"""Tick materializer: a PcrRun becomes the shared run record, and the record becomes sheets.

This is the one unbuilt piece named in research/tick-observability-ledger.md:60-85
("What pyto's Python side lacks: a Tick materializer"). Everything a per-Tick view
needs is already computed and in memory at the end of `PCR.run` -- the Tick boundary
and order (`PcrRun.ticks`), the values (`PcrRun.results`), the writer and the reads
(`PcrRun.receipts` when `observe=True`), and the store (`PxC`) -- and nothing joined
it or rendered it. `run_record` joins it; `write_record` writes it; `tick_sheets`
renders it.

The output document is `pyto-run-record@1`, specified in pyto/viewer/RECORD.md and
read by both runtimes. This module is an adapter onto that schema, never a second
schema: fields absent from RECORD.md are not added here, and fields RECORD.md
declares are emitted as null when this runtime did not observe them ("Missing
fields are null, never invented", RECORD.md:65).

The record is *derived*: it is an inspection view of a program and a run, never the
program itself (RECORD.md:11-12). It reads `PcrRun` and never mutates it, so the
testimony bytes consumers embed -- `json.dumps([asdict(t) for t in run.ticks])`
(pcr.py:130-140) -- are unaffected by materializing.

Every field of the annotation anchor of research/tick-observability-ledger.md:91-93,
`(pcr, tick.name, invocation.id, part.address)`, is present in the emitted document
and in the title of every panel `tick_sheets` draws, so a note left against a sheet
addresses the same identities the execution used.

Pillow is optional. Importing this module never imports PIL (`pyto.neon` imports it
at module level, so the import here is deferred into the functions that draw):
`run_record` degrades an image value to `omitted` with a note when Pillow is absent,
and `tick_sheets` -- which cannot degrade, it only draws -- raises RuntimeError.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
from typing import Any, Iterable, Mapping

from .core import PxC
from .pcr import PcrRun

SCHEMA = "pyto-run-record@1"
RUNTIME = "pyto"
VALUE_CAP_BYTES = 262144  # RECORD.md:63 -- 256 KB
ARRAY_CAP = 200  # RECORD.md:64
PNG_DATA_URL_PREFIX = "data:image/png;base64,"  # RECORD.md:60-61, adapters.js:26

__all__ = ["SCHEMA", "run_record", "write_record", "tick_sheets"]


# --- values --------------------------------------------------------------------


def _is_pil_image(value: Any) -> bool:
    """True for a PIL.Image.Image without importing PIL.

    Duck-typed on the class's module so that a value produced by a Pillow that is
    installed in the *producing* process is still recognized here; the actual
    conversion below imports PIL and reports its absence in the note.
    """
    module = getattr(type(value), "__module__", "") or ""
    if not (module == "PIL" or module.startswith("PIL.")):
        return False
    return all(hasattr(value, attribute) for attribute in ("save", "mode", "size"))


def _is_svg(text: str) -> bool:
    stripped = text.lstrip()
    if stripped.startswith("<svg"):
        return True
    return stripped.startswith("<?xml") and "<svg" in stripped


def _stable_repr(value: Any) -> str:
    """A repr with the unordered containers ordered, for digesting a non-JSON value.

    `repr(value)` alone is not a defensible digest input for a set: str hashing is
    salted per process (PYTHONHASHSEED), so the same set reprs differently in two
    processes and the digest would say two identical values differ. Sets and dict
    keys are therefore sorted by their own element repr before digesting. This is a
    digest of a *rendering*, not of the value, and the note says so.
    """
    if isinstance(value, (set, frozenset)):
        return "{" + ", ".join(sorted(_stable_repr(item) for item in value)) + "}"
    if isinstance(value, dict):
        items = sorted((_stable_repr(k), _stable_repr(v)) for k, v in value.items())
        return "{" + ", ".join(f"{k}: {v}" for k, v in items) + "}"
    if isinstance(value, (list, tuple)):
        inner = ", ".join(_stable_repr(item) for item in value)
        return f"[{inner}]" if isinstance(value, list) else f"({inner})"
    return repr(value)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _truncate_arrays(value: Any, cap: int, lengths: list[int]) -> Any:
    """Copy `value` with every list longer than `cap` cut to its first `cap` entries.

    Recursive: a long array nested inside a dict is truncated too, and every original
    length is appended to `lengths` so the note can carry them.
    """
    if isinstance(value, list):
        if len(value) > cap:
            lengths.append(len(value))
            value = value[:cap]
        return [_truncate_arrays(item, cap, lengths) for item in value]
    if isinstance(value, dict):
        return {key: _truncate_arrays(item, cap, lengths) for key, item in value.items()}
    return value


def _png_data_url(image: Any) -> str:
    from PIL import Image  # noqa: F401 - raises ImportError when Pillow is absent

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return PNG_DATA_URL_PREFIX + base64.b64encode(buffer.getvalue()).decode("ascii")


def _omitted(note: str) -> dict[str, Any]:
    return {"kind": "omitted", "data": None, "note": note}


def render_value(
    value: Any,
    *,
    value_cap_bytes: int = VALUE_CAP_BYTES,
    array_cap: int = ARRAY_CAP,
) -> dict[str, Any]:
    """One `value` object of RECORD.md: `{kind, data, note}`.

    Dispatch order, which is not the order RECORD.md:59-64 lists the kinds in
    because `str` is itself JSON-serializable and would otherwise never reach
    `text`: image first (it is a type test), then `str` (`svg` when it opens an SVG
    document, else `text`), then JSON-serializable (`json`), then `omitted`.

    Arrays are truncated before the size cap is applied, so a long array of small
    entries survives as its first `array_cap` entries rather than being dropped
    whole.
    """
    note: str | None = None

    if _is_pil_image(value):
        try:
            data = _png_data_url(value)
        except ImportError:  # pragma: no cover - Pillow present in this checkout
            return _omitted("image value: Pillow is not installed, so no PNG could be encoded")
        except Exception as error:  # a truncated or unsupported image mode
            return _omitted(f"image value could not be encoded as PNG: {type(error).__name__}: {error}")
        return _capped({"kind": "png-data-url", "data": data, "note": None}, value_cap_bytes)

    if isinstance(value, str):
        # The order and the tests are adapters.js:262-264's, which is the
        # reference (ULTRACODE-WEEK.md Reframing 4, "JS is first class"): svg
        # first, then a PNG data URL, else text. Without the second test a
        # string that is already a rendered image is `text` in a pyto record and
        # `png-data-url` in a DiscStudio one, and the same Part shows as a wall
        # of base64 in one viewer pane and as a picture in the other.
        if _is_svg(value):
            kind = "svg"
        elif value.startswith(PNG_DATA_URL_PREFIX):
            kind = "png-data-url"
        else:
            kind = "text"
        return _capped({"kind": kind, "data": value, "note": None}, value_cap_bytes)

    lengths: list[int] = []
    try:
        json.dumps(value)
    except (TypeError, ValueError) as error:
        rendering = _stable_repr(value)
        return _omitted(
            f"not JSON-serializable ({type(value).__name__}: {error}); "
            f"sha256 of a canonical repr = {_digest(rendering)}"
        )
    data = _truncate_arrays(value, array_cap, lengths)
    if lengths:
        note = (
            f"{len(lengths)} array(s) truncated to the first {array_cap} entries; "
            f"original lengths: {sorted(lengths, reverse=True)}"
        )
    return _capped({"kind": "json", "data": data, "note": note}, value_cap_bytes)


def _capped(rendered: dict[str, Any], value_cap_bytes: int) -> dict[str, Any]:
    """Replace an over-cap rendering with `omitted`, carrying its size and digest."""
    data = rendered["data"]
    payload = data if isinstance(data, str) else json.dumps(data, sort_keys=True, separators=(",", ":"))
    size = len(payload.encode("utf-8"))
    if size <= value_cap_bytes:
        return rendered
    note = (
        f"{rendered['kind']} value is {size} bytes, over the {value_cap_bytes} byte cap; "
        f"sha256 = {_digest(payload)}"
    )
    if rendered["note"]:
        note = f"{note}; {rendered['note']}"
    return _omitted(note)


# --- the record ----------------------------------------------------------------


def _runtime_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - stdlib since 3.8
        return "unknown"
    for name in ("pyto-lab", "pyto"):
        try:
            return version(name)
        except PackageNotFoundError:
            continue
        except Exception:  # pragma: no cover - a broken installation is not fatal here
            break
    return "unknown"


def run_record(
    run: PcrRun,
    pxc: PxC,
    *,
    preexisting: set[str] | None = None,
    pcr_name: str | None = None,
    source: dict | None = None,
    value_cap_bytes: int = VALUE_CAP_BYTES,
    array_cap: int = ARRAY_CAP,
) -> dict:
    """The `pyto-run-record@1` document for one executed PCR.

    `run` is what `PCR.run(pxc, observe=True)` returned; `pxc` is the store it ran
    against, read only to infer `preexisting` when it is not given. Pass
    `preexisting=set(pxc.addresses())` captured *before* the run for the accurate
    answer (RECORD.md:73); the fallback here is "every address the post-run store
    holds that no invocation of this run produced", which is right whenever the run
    did not overwrite a seeded Part.

    Joins, in the order RECORD.md needs them:

    - the Tick boundary, its name and its `index` come from `run.ticks` position
      (pcr.py:63-78); the invocation order inside a Tick is declaration order;
    - each invocation is joined to `run.receipts[id]` by invocation id -- the join
      nothing in pyto did before (ledger:69);
    - the value is `run.results[id]` rendered by `render_value`;
    - `hit` is the owner's definition (ULTRACODE-WEEK.md:79-82, RECORD.md:53-56):
      a `px:` binding whose address this run had not produced yet, or that is in
      `preexisting`. Reading `fn:<id>` is not a hit: that Part was computed here.

    Without receipts (`observe=False`) the document is still emitted, with the
    observed-only fields null rather than guessed.
    """
    into_by_id: dict[str, str | None] = {}
    for tick in run.ticks:
        for testimony in tick.calculations:
            into_by_id[testimony.id] = testimony.into

    if preexisting is None:
        produced_anywhere = {address for address in into_by_id.values() if address}
        preexisting = {address for address in pxc.addresses() if address not in produced_anywhere}
    preexisting = set(preexisting)

    produced_so_far: set[str] = set()
    read_by: dict[str, list[str]] = {}
    written_by: dict[str, str] = {}
    touched: list[str] = []  # every address named anywhere, in first-seen order

    def touch(address: str) -> None:
        if address not in read_by:
            read_by[address] = []
            touched.append(address)

    ticks: list[dict[str, Any]] = []
    invocation_count = 0
    hit_count = 0
    wall_ms: float | None = None

    for index, tick in enumerate(run.ticks):
        invocations: list[dict[str, Any]] = []
        for testimony in tick.calculations:
            receipt = run.receipts.get(testimony.id)
            invocation_count += 1

            px_reads = [
                spelling.removeprefix("px:")
                for spelling in testimony.inputs.values()
                if spelling.startswith("px:")
            ]
            fn_reads = [
                spelling.removeprefix("fn:")
                for spelling in testimony.inputs.values()
                if spelling.startswith("fn:")
            ]
            hit = any(
                address in preexisting or address not in produced_so_far for address in px_reads
            )
            if hit:
                hit_count += 1

            for address in px_reads:
                touch(address)
                if testimony.id not in read_by[address]:
                    read_by[address].append(testimony.id)
            for writer in fn_reads:
                # pcr.py:112-116 rewrote a binding on an already-declared Part into
                # its writer's ResultRef, so `fn:<id>` is a read of that writer's
                # `into` Part -- which is why RECORD.md:44 lists fit/score under the
                # split Part's `read_by`.
                address = into_by_id.get(writer)
                if address:
                    touch(address)
                    if testimony.id not in read_by[address]:
                        read_by[address].append(testimony.id)
            if receipt is not None:
                for address in receipt.actual_consumes:
                    touch(address)
                    if testimony.id not in read_by[address]:
                        read_by[address].append(testimony.id)

            produces: Iterable[str] = (
                receipt.actual_produces
                if receipt is not None
                else ((testimony.into,) if testimony.into else ())
            )
            for address in produces:
                touch(address)
                written_by[address] = testimony.id
                produced_so_far.add(address)

            if receipt is not None:
                calculation = {
                    "address": receipt.calculation.address,
                    "implementation_sha256": receipt.calculation.implementation_sha256,
                    "identity_scope": receipt.calculation.identity_scope,
                }
                declared_consumes: list[str] | None = [
                    f"px:{address}" for address in receipt.declared_consumes
                ]
                actual_consumes: list[str] | None = list(receipt.actual_consumes)
                actual_produces: list[str] | None = list(receipt.actual_produces)
                writes: list[dict[str, str]] | None = [
                    {"address": write.address, "kind": write.kind} for write in receipt.writes
                ]
                duration_ms: float | None = receipt.duration_ms
                result_sha256: str | None = receipt.result_sha256
                wall_ms = receipt.duration_ms if wall_ms is None else wall_ms + receipt.duration_ms
            else:
                # observe=False: the identity is the authored address only, and every
                # observed-only field is null. RECORD.md:65.
                calculation = {
                    "address": testimony.calculation,
                    "implementation_sha256": None,
                    "identity_scope": None,
                }
                declared_consumes = [f"px:{address}" for address in px_reads]
                actual_consumes = None
                actual_produces = None
                writes = None
                duration_ms = None
                result_sha256 = None

            invocations.append(
                {
                    "id": testimony.id,
                    "calculation": calculation,
                    "inputs": dict(testimony.inputs),
                    "args": dict(testimony.args),
                    "into": testimony.into,
                    "declared_consumes": declared_consumes,
                    "actual_consumes": actual_consumes,
                    "actual_produces": actual_produces,
                    "writes": writes,
                    "duration_ms": duration_ms,
                    "result_sha256": result_sha256,
                    "hit": hit,
                    "value": render_value(
                        run.results.get(testimony.id),
                        value_cap_bytes=value_cap_bytes,
                        array_cap=array_cap,
                    )
                    if testimony.id in run.results
                    else _omitted("the run retained no result for this invocation"),
                }
            )
        ticks.append({"index": index, "name": tick.name, "invocations": invocations})

    parts = {
        address: {
            "written_by": written_by.get(address),
            "read_by": read_by[address],
            "preexisting": address in preexisting,
        }
        for address in touched
    }

    document_source = {"runtime": RUNTIME, "version": _runtime_version(), "commit": None}
    if source:
        document_source.update(source)

    return {
        "schema": SCHEMA,
        "pcr": pcr_name if pcr_name is not None else run.pcr,
        "source": document_source,
        "ticks": ticks,
        "parts": parts,
        "counters": {
            "invocations": invocation_count,
            "hits": hit_count,
            "computed": invocation_count - hit_count,
            "wall_ms": wall_ms,
        },
    }


def write_record(record: Mapping[str, Any], path: str) -> str:
    """Write `record` as JSON with sorted keys, two-space indent and LF (RECORD.md:67)."""
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


# --- sheets --------------------------------------------------------------------


def _neon():
    """Import the neon kit, reporting the missing optional dependency plainly."""
    try:
        from . import neon
    except ImportError as error:  # pragma: no cover - Pillow present in this checkout
        raise RuntimeError(
            "tick_sheets needs Pillow (pyto.neon imports PIL); the record itself needs no "
            f"image library: {error}"
        ) from error
    return neon


def _safe(name: str) -> str:
    return "".join(character if character.isalnum() or character in "-._" else "-" for character in name)


def _wrap(text: str, width: int = 108) -> list[str]:
    return [text[start:start + width] for start in range(0, max(len(text), 1), width)]


def _invocation_lines(record: Mapping[str, Any], tick: Mapping[str, Any], invocation: Mapping[str, Any]) -> list[str]:
    """The text of one invocation panel: the anchor, then what it read, wrote and cost."""
    calculation = invocation["calculation"]
    duration = invocation["duration_ms"]
    reads = invocation["actual_consumes"]
    if reads is None:
        reads = [spelling for spelling in invocation["inputs"].values()]
    writes = invocation["writes"]
    write_text = (
        ", ".join(f"{write['address']} ({write['kind']})" for write in writes)
        if writes
        else (invocation["into"] or "-")
    )
    lines = [
        f"anchor  {record['pcr']} | {tick['name']} | {invocation['id']} | {invocation['into'] or '-'}",
        f"calc    {calculation['address']}  sha256={(calculation['implementation_sha256'] or 'none')[:12]}",
        f"inputs  {json.dumps(invocation['inputs'], sort_keys=True)}",
        f"args    {json.dumps(invocation['args'], sort_keys=True)}",
        f"reads   {', '.join(reads) if reads else '-'}",
        f"writes  {write_text}",
        f"cost    {'null' if duration is None else format(duration, '.3f') + ' ms'}"
        f"   result_sha256={(invocation['result_sha256'] or 'none')[:12]}",
        f"HIT     {invocation['hit']}",
        f"value   kind={invocation['value']['kind']}"
        + (f"  note={invocation['value']['note']}" if invocation["value"]["note"] else ""),
    ]
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(_wrap(line))
    wrapped.extend(_value_preview(invocation["value"]))
    return wrapped


def _value_preview(value: Mapping[str, Any], lines: int = 3, width: int = 108) -> list[str]:
    """The first `lines` wrapped lines of a json/text value, so the panel shows material.

    "Neon first" (neon.py:1-6) applies to numbers too: a panel that names a value's
    kind but never shows it is the value-blindness the ledger records
    (research/tick-observability-ledger.md:107-118). Image and SVG values get their
    own panel instead, and an omitted value has nothing to show.
    """
    if value["kind"] == "json":
        text = json.dumps(value["data"], sort_keys=True)
    elif value["kind"] == "text":
        text = value["data"]
    else:
        return []
    chunks = _wrap(text, width)
    body = [f"        {chunk}" for chunk in chunks[:lines]]
    if len(chunks) > lines:
        body[-1] = body[-1] + " ..."
    return body


def _text_panel(neon, title: str, lines: list[str], *, hit: bool, width: int = 700) -> Any:
    from PIL import Image, ImageDraw

    line_height = 13
    pad = 8
    body = Image.new("RGBA", (width, pad * 2 + line_height * max(len(lines), 1)), (12, 12, 12, 255))
    draw = ImageDraw.Draw(body)
    for index, line in enumerate(lines):
        colour = neon.GREY
        if line.startswith("HIT"):
            colour = neon.MAGENTA if hit else neon.GREY
        elif line.startswith(("anchor", "calc")):
            colour = neon.CYAN
        elif line.startswith(("writes", "value")):
            colour = neon.GREEN
        draw.text((pad, pad + index * line_height), line, fill=colour, font=neon.FONT)
    return neon.panel(title, body, width=width)


def _value_image(neon, value: Mapping[str, Any]) -> Any | None:
    from PIL import Image

    if value["kind"] != "png-data-url" or not isinstance(value["data"], str):
        return None
    _, _, payload = value["data"].partition(",")
    return Image.open(io.BytesIO(base64.b64decode(payload))).convert("RGBA")


def tick_sheets(record: Mapping[str, Any], out_dir: str, *, cols: int = 2) -> list[str]:
    """One PNG per Tick under `out_dir`; returns every path written, sorted.

    Each sheet carries one text panel per invocation (the anchor, the reads, the
    writes, the duration, the hit) plus an image panel for every value the record
    rendered as an image.

    SVG is the one value kind this function cannot draw: rasterizing SVG needs a
    renderer pyto does not depend on. The document text is written verbatim beside
    the sheet as `<sheet stem>.<invocation id>.svg` and a placeholder panel names
    that file, so the harness (or a browser) can rasterize it. The record's SVG is
    never modified, and it is never inlined as markup.
    """
    neon = _neon()
    os.makedirs(out_dir, exist_ok=True)
    written: list[str] = []

    for tick in record["ticks"]:
        stem = f"tick-{tick['index']:03d}-{_safe(tick['name'])}"
        panels = []
        for invocation in tick["invocations"]:
            title = f"{tick['index']}/{tick['name']}  {invocation['id']}"
            panels.append(
                _text_panel(
                    neon,
                    title,
                    _invocation_lines(record, tick, invocation),
                    hit=bool(invocation["hit"]),
                )
            )
            value = invocation["value"]
            image = _value_image(neon, value)
            if image is not None:
                panels.append(neon.panel(f"{title}  value ({value['kind']})", image))
            elif value["kind"] == "svg" and isinstance(value["data"], str):
                svg_name = f"{stem}.{_safe(invocation['id'])}.svg"
                svg_path = os.path.join(out_dir, svg_name)
                with open(svg_path, "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(value["data"])
                written.append(svg_path)
                panels.append(
                    _text_panel(
                        neon,
                        f"{title}  value (svg)",
                        _wrap(
                            f"svg written to {svg_name}; the library does not rasterize SVG "
                            "(no renderer dependency). Rasterize it in the harness or view it in a browser."
                        ),
                        hit=False,
                    )
                )
        if not panels:
            panels.append(_text_panel(neon, f"{tick['index']}/{tick['name']}", ["(no invocations)"], hit=False))
        path = os.path.join(out_dir, f"{stem}.png")
        neon.sheet(panels, cols=cols).save(path)
        written.append(path)

    return sorted(written)
