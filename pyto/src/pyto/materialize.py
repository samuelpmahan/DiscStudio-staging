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
schema: fields absent from RECORD.md are not added here, and only the fields
RECORD.md marks nullable are ever null ("Missing fields are null, never
invented", RECORD.md:65, licenses null for a declared-nullable field -- not for
`identity_scope`, `actual_consumes`, `actual_produces` or `writes`, which is why
`run_record` requires `observe=True` rather than nulling them).

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
from typing import Any, Mapping

from .core import PxC
from .pcr import PcrRun, array_sha256, is_array, receipt_address

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


def _stable_repr(value: Any, _active: set[int] | None = None) -> str:
    """A repr with the unordered containers ordered, for digesting a non-JSON value.

    `repr(value)` alone is not a defensible digest input for a set: str hashing is
    salted per process (PYTHONHASHSEED), so the same set reprs differently in two
    processes and the digest would say two identical values differ. Sets and dict
    keys are therefore sorted by their own element repr before digesting. This is a
    digest of a *rendering*, not of the value, and the note says so.

    `_active` is the id() memo of the containers currently on the recursion stack.
    Builtin `repr()` carries one -- `repr()` of a self-referential dict is
    `{'name': 'node', 'self': {...}}`, not a RecursionError -- and this rendering
    has to carry one too: without it a cyclic value recursed until the interpreter
    gave up, and the RecursionError escaped `render_value` and took the whole
    record down (the JS reference returns `omitted` for the same value,
    adapters.js:281-295).
    """
    if _active is None:
        _active = set()
    marker = id(value)
    if isinstance(value, (set, frozenset)):
        if marker in _active:
            return "{...}"
        _active.add(marker)
        try:
            return "{" + ", ".join(sorted(_stable_repr(item, _active) for item in value)) + "}"
        finally:
            _active.discard(marker)
    if isinstance(value, dict):
        if marker in _active:
            return "{...}"
        _active.add(marker)
        try:
            items = sorted(
                (_stable_repr(k, _active), _stable_repr(v, _active)) for k, v in value.items()
            )
            return "{" + ", ".join(f"{k}: {v}" for k, v in items) + "}"
        finally:
            _active.discard(marker)
    if isinstance(value, (list, tuple)):
        if marker in _active:
            return "[...]" if isinstance(value, list) else "(...)"
        _active.add(marker)
        try:
            inner = ", ".join(_stable_repr(item, _active) for item in value)
            return f"[{inner}]" if isinstance(value, list) else f"({inner})"
        finally:
            _active.discard(marker)
    return repr(value)


def _unserializable_note(value, error: BaseException) -> str:
    """The `omitted` note for a value json.dumps refused, digesting what it can.

    Every step here is a step that can itself fail on a hostile value (a __repr__
    that raises, a structure too deep to render at all), and a failure to describe
    a value must not be worse than the value: the note degrades, the record stands.
    """
    try:
        reason = f"not JSON-serializable ({type(value).__name__}: {error})"
    except Exception:  # pragma: no cover - a __str__ that raises
        reason = f"not JSON-serializable ({type(error).__name__})"
    try:
        return f"{reason}; sha256 of a canonical repr = {_digest(_stable_repr(value))}"
    except Exception as second:
        return f"{reason}; no canonical repr could be taken either ({type(second).__name__})"


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
        # A list with no list and no dict under it is its own truncation, and one
        # C-level pass over its types says so far more cheaply than recursing once
        # per entry: a genome's 196,608 rgb integers were rebuilt one call at a
        # time to produce the same list back.
        if not any(issubclass(kind, (list, dict)) for kind in set(map(type, value))):
            return value
        return [_truncate_arrays(item, cap, lengths) for item in value]
    if isinstance(value, dict):
        return {key: _truncate_arrays(item, cap, lengths) for key, item in value.items()}
    return value


class _EncodeStopped(Exception):
    """Raised by `_CappedSink` inside the encoder once the output passes the cap."""


class _CappedSink:
    """A file object for `Image.save` that accepts at most `limit` bytes.

    PIL hands its encoder's output to `fp.write` block by block
    (`ImageFile._save`), so refusing the block that crosses the limit stops the
    encode where it stands. That is what makes "never encode an image that cannot
    fit" true rather than aspirational: a 1024x1024 photograph is three megabytes
    of pixels whose PNG is megabytes more, and the old path compressed all of it,
    base64'd all of it, measured it, and threw it away.
    """

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.size = 0
        self.blocks: list[bytes] = []

    def write(self, data: Any) -> int:
        self.size += len(data)
        if self.size > self.limit:
            raise _EncodeStopped
        self.blocks.append(bytes(data))
        return len(data)

    def tell(self) -> int:
        return self.size

    def flush(self) -> None:  # pragma: no cover - PIL calls it, it has nothing to do
        pass

    def value(self) -> bytes:
        return b"".join(self.blocks)


def _png_budget(value_cap_bytes: int) -> int:
    """The largest PNG, in bytes, whose data URL still fits under the cap.

    base64 spends four characters on every three bytes, so the data URL of an
    n-byte PNG is `len(prefix) + 4 * ceil(n / 3)` bytes, every one of them ASCII.
    Solving that for n is exact, and exactness is the point: an encoding one byte
    longer than this is over the cap and one this long is under it, so which side
    of the cap an image falls on is decided by the encoder's own output length and
    never by a guess about how well an image compresses.
    """
    return max(0, (value_cap_bytes - len(PNG_DATA_URL_PREFIX)) // 4 * 3)


def _png_data_url(image: Any, limit: int | None = None) -> str | None:
    """The image as a `data:image/png;base64,...` string, or None when it is over `limit`.

    `limit` is a PNG byte budget (`_png_budget`), not a data URL budget: the encode
    stops as soon as the PNG passes it, before there is anything to base64.
    """
    from PIL import Image  # noqa: F401 - raises ImportError when Pillow is absent

    if limit is None:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        payload = buffer.getvalue()
    else:
        sink = _CappedSink(limit)
        try:
            image.save(sink, format="PNG")
        except _EncodeStopped:
            return None
        payload = sink.value()
    return PNG_DATA_URL_PREFIX + base64.b64encode(payload).decode("ascii")


def _image_digest(image: Any) -> str:
    """sha256 of an image's mode, its size and its raw pixels.

    The digest an over-cap image carries. The old path digested the base64 it had
    just built and was about to throw away, which is the encode this module no
    longer performs; this one reads the pixels the image already holds. Same
    pixels, same mode, same size digest the same, and nothing else does -- but it
    is a digest of the *image* and not of any PNG of it, so the note says which it
    is (pyto/viewer/RECORD.md, "over the size cap").
    """
    digest = hashlib.sha256()
    digest.update(f"{image.mode} {image.size[0]}x{image.size[1]} ".encode("utf-8"))
    digest.update(image.tobytes())
    return digest.hexdigest()


def _over_cap_image_note(image: Any, value_cap_bytes: int, limit: int) -> str:
    try:
        identity = f"{image.mode} {image.size[0]}x{image.size[1]}"
    except Exception:  # pragma: no cover - a PIL image always has both
        identity = type(image).__name__
    note = (
        f"image value ({identity}) is over the {value_cap_bytes} byte cap: its PNG passed "
        f"{limit} bytes, which base64 only makes longer, so the encoding was stopped and "
        "dropped"
    )
    try:
        return f"{note}; sha256 of the raw pixels = {_image_digest(image)}"
    except Exception as error:  # a truncated image cannot hand over its pixels
        return f"{note}; no digest of the raw pixels could be taken ({type(error).__name__})"


def _array_preview(value: Any, cap: int) -> list[Any] | None:
    """The first `cap` entries of the array, flattened, or None when they are not JSON.

    Only the dtypes whose Python values are JSON -- bool, the integers, the floats
    -- get a preview; a complex, datetime or structured array is described and
    digested but not previewed, because a preview that cannot be written is worse
    than none (the record is dumped whole at the end, and one unserializable entry
    would lose all of it).
    """
    if getattr(value.dtype, "kind", "") not in ("b", "i", "u", "f"):
        return None
    try:
        return value.reshape(-1)[:cap].tolist()
    except Exception:  # pragma: no cover - an array this runtime cannot flatten
        return None


def _array_href(values_path: str) -> str:
    """What the record says the sidecar is: the folder beside the record, and the file.

    A path relative to the record's own directory, so a record and its `.values`
    folder are moved, copied and served together.
    """
    directory, name = os.path.split(values_path)
    return f"{os.path.basename(directory)}/{name}" if directory else name


def _array_value(
    value: Any,
    *,
    value_cap_bytes: int,
    array_cap: int,
    digest: str | None,
    values_path: str | None,
) -> dict[str, Any]:
    """One `array` value of RECORD.md: what the array is, its digest, a preview, its bytes.

    An array is not rendered as JSON and never becomes `omitted` for its size: a
    256x256x3 render is 196,608 numbers, and spelling them as decimal text is what
    turned one generation's record into 109 MiB of integers that no viewer could
    open. What the record keeps instead is what an inspection needs -- the dtype,
    the shape, the digest, and the first `array_cap` values -- with the buffer
    itself written beside the record when the caller asked for it
    (`run_record(values_dir=...)`).

    `digest` is the receipt's `result_sha256`, already computed by `pcr.array_sha256`
    over these very bytes: the array is digested once per run, not once per reader.
    """
    shape = tuple(int(extent) for extent in value.shape)
    count = 1
    for extent in shape:
        count *= extent
    dtype = str(value.dtype)
    if digest is None:
        digest = array_sha256(value)
    # The preview is the first `ARRAY_CAP` values at most, however high the
    # caller's `array_cap` is: `array_cap` raises how much of a JSON *list* the
    # record spells out, and an array is not spelled out at all -- its buffer is
    # beside the record. The owner's own generation passes array_cap=250000, which
    # under the other reading writes all 196,608 numbers of every render back into
    # the record and loses the whole point of the kind ({?} ArrayPreviewCap).
    preview = _array_preview(value, min(array_cap, ARRAY_CAP))
    data: dict[str, Any] = {
        "dtype": dtype,
        "shape": list(shape),
        "digest": digest,
        "preview": preview,
        "path": None,
    }
    notes = [f"{count} {dtype} value(s), shape ({', '.join(str(e) for e in shape)})"]
    if values_path is not None:
        try:
            directory = os.path.dirname(os.path.abspath(values_path))
            os.makedirs(directory, exist_ok=True)
            with open(values_path, "wb") as handle:
                handle.write(value.tobytes())
            data["path"] = _array_href(values_path)
            notes.append(f"raw bytes at {data['path']}")
        except Exception as error:  # a full disk is not a reason to lose the record
            notes.append(f"the raw bytes could not be written ({type(error).__name__}: {error})")
    else:
        notes.append("the raw bytes were not kept (no values directory was given)")
    if preview is None:
        notes.append(f"no preview: dtype {dtype} does not render as JSON")
    else:
        notes.append(f"preview holds the first {len(preview)} of {count}")
    rendered = {"kind": "array", "data": data, "note": "; ".join(notes)}
    # The description is bounded by `array_cap`, but a caller who raises that cap
    # can still ask for more preview than the value cap allows. The preview goes
    # and the description stays: an `array` never degrades to `omitted`, because
    # the dtype, the shape and the digest are the part a reader cannot recompute.
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    if len(payload.encode("utf-8")) > value_cap_bytes:
        data["preview"] = None
        notes[-1] = (
            f"the preview of {len(preview or ())} value(s) was over the {value_cap_bytes} "
            "byte cap and was dropped"
        )
        rendered["note"] = "; ".join(notes)
    return rendered


def _omitted(note: str) -> dict[str, Any]:
    return {"kind": "omitted", "data": None, "note": note}


def render_value(
    value: Any,
    *,
    value_cap_bytes: int = VALUE_CAP_BYTES,
    array_cap: int = ARRAY_CAP,
    result_sha256: str | None = None,
    values_path: str | None = None,
) -> dict[str, Any]:
    """One `value` object of RECORD.md: `{kind, data, note}`.

    Dispatch order, which is not the order RECORD.md:59-64 lists the kinds in
    because `str` is itself JSON-serializable and would otherwise never reach
    `text`: image first (it is a type test), then array (a type test too), then
    `str` (`svg` when it opens an SVG document, else `text`), then
    JSON-serializable (`json`), then `omitted`.

    Arrays are truncated before the size cap is applied, so a long array of small
    entries survives as its first `array_cap` entries rather than being dropped
    whole.

    `result_sha256` is the receipt's digest of this same value, passed in by
    `run_record`. It says one thing and buys one thing: the value dumped once
    already, so this function does not dump it again to find out whether it is
    JSON. A value big enough to matter -- a genome's million floats -- was being
    serialized three times to produce one record line.

    `values_path` is where an array value's raw bytes go, `None` to keep none.
    """
    note: str | None = None

    if _is_pil_image(value):
        limit = _png_budget(value_cap_bytes)
        try:
            data = _png_data_url(value, limit=limit)
        except ImportError:  # pragma: no cover - Pillow present in this checkout
            return _omitted("image value: Pillow is not installed, so no PNG could be encoded")
        except Exception as error:  # a truncated or unsupported image mode
            return _omitted(f"image value could not be encoded as PNG: {type(error).__name__}: {error}")
        if data is None:
            return _omitted(_over_cap_image_note(value, value_cap_bytes, limit))
        return _capped({"kind": "png-data-url", "data": data, "note": None}, value_cap_bytes)

    if is_array(value):
        return _array_value(
            value,
            value_cap_bytes=value_cap_bytes,
            array_cap=array_cap,
            digest=result_sha256,
            values_path=values_path,
        )

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
    # `except Exception`, not `(TypeError, ValueError)`: RECORD.md:62 assigns every
    # unserializable value to `omitted`, and a value that is merely awkward -- a
    # reference cycle, a structure nested past the recursion limit, a __getattr__
    # that raises -- must degrade to `omitted` here rather than escape and lose the
    # whole record. json.dumps raises RecursionError (not a ValueError) on both of
    # the first two, which is exactly how the record used to be lost.
    # The digest is the dump: `pcr._result_sha256` is `json.dumps(value, ...)` over
    # the very object `run.results` holds, and it is None exactly when that dump
    # raised. A digest is therefore proof that the value is JSON-serializable and
    # this test is skipped. The converse is not proof and is not treated as one:
    # `sort_keys=True` also refuses a dict whose keys cannot be compared with each
    # other, which plain `json.dumps` accepts, so a value with no digest still
    # takes the old path and is still `json` when it dumps.
    if result_sha256 is None:
        try:
            json.dumps(value)
        except Exception as error:
            return _omitted(_unserializable_note(value, error))
    try:
        data = _truncate_arrays(value, array_cap, lengths)
        if lengths:
            note = (
                f"{len(lengths)} array(s) truncated to the first {array_cap} entries; "
                f"original lengths: {sorted(lengths, reverse=True)}"
            )
        return _capped({"kind": "json", "data": data, "note": note}, value_cap_bytes)
    except Exception as error:  # pragma: no cover - json.dumps already accepted it
        return _omitted(
            f"JSON value could not be rendered: {type(error).__name__}: {error}"
        )


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


def _produce_addresses(into: Any) -> tuple[str, ...]:
    """The addresses one invocation's `into` names: none, one, or several.

    `CalculationTestimony.into` is an address, a tuple of addresses (an invocation
    that publishes several Parts from one pass) or None; the record spells the
    second as a JSON array (pyto/viewer/RECORD.md).
    """
    if into is None:
        return ()
    if isinstance(into, str):
        return (into,)
    return tuple(into)


def _fn_read_addresses(spelling: str, produces_by_id: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
    """The Part addresses an `fn:` binding reads, resolved through the producer.

    The two spellings RECORD.md fixes: `fn:<id>` is the producer's whole result --
    legal only where that producer publishes at most one Part -- and
    `fn:<id>#<address>` names one produce of a producer that published several. A
    known id wins over the `#` split, so an invocation id that itself carries a `#`
    still resolves as the bare reference it is.
    """
    body = spelling.removeprefix("fn:")
    if body in produces_by_id:
        return produces_by_id[body]
    writer, separator, address = body.rpartition("#")
    if separator and address and address in produces_by_id.get(writer, ()):
        return (address,)
    return ()


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
    values_dir: str | None = None,
) -> dict:
    """The `pyto-run-record@1` document for one executed PCR.

    `run` is what `PCR.run(pxc, observe=True)` returned; `pxc` is the store it ran
    against, read only to infer `preexisting` when it is not given. `values_dir` is
    where the raw bytes of `array` values go, one `<address>.bin` per value, and
    the record names each one relative to its own directory; without it an array is
    still described and digested, but its buffer is not kept. The bytes are written
    here and not by `write_record` because this is the only place that has both the
    values and a path to put them ({?} ArraySidecarWriter). Pass
    `preexisting=set(pxc.addresses())` captured *before* the run for the accurate
    answer (RECORD.md:73); the fallback here is "every address the post-run store
    holds that no invocation of this run produced", which is right whenever the run
    did not overwrite a seeded Part. The Parts this run's own observation wrote
    under the reserved `px.receipt.` segment are excluded from that fallback for
    the same reason the produced addresses are: they did not preexist the run.

    Joins, in the order RECORD.md needs them:

    - the Tick boundary, its name and its `index` come from `run.ticks` position
      (pcr.py:63-78); the invocation order inside a Tick is declaration order;
    - each invocation is joined to `run.receipts[id]` by invocation id -- the join
      nothing in pyto did before (ledger:69);
    - the value is `run.results[id]` rendered by `render_value`;
    - `hit` is the JS reference rule, `adapters.js:244-249 deriveHit`, which is the
      RECORD.md:55-56 rule verbatim: a `px:` binding whose address was not produced
      by an earlier invocation of the same run. Reading `fn:<id>` is not a hit (that
      Part was computed here), and neither is re-reading a `preexisting` address
      this run has already overwritten -- nothing was reused, and RECORD.md's own
      parenthetical excludes it. `preexisting` decides `parts[...].preexisting`
      only; the two runtimes agree row for row.

    `run.receipts` is required: `PCR.run(pxc, observe=True)`. Without it this
    runtime could only emit `calculation.identity_scope`, `actual_consumes`,
    `actual_produces` and `writes` as null -- four fields RECORD.md does not mark
    nullable and the reference reader (`adapters.js validate`) refuses -- so a
    receipt-less run raises instead of producing a document that claims a schema it
    does not satisfy.
    """
    missing = [
        testimony.id
        for tick in run.ticks
        for testimony in tick.calculations
        if testimony.id not in run.receipts
    ]
    if missing:
        raise ValueError(
            f"run_record needs the receipts of the run it describes; {len(missing)} of "
            f"{sum(len(tick.calculations) for tick in run.ticks)} invocation(s) have none "
            f"(first: {missing[0]!r}). Call PCR.run(pxc, observe=True). Without receipts "
            "this runtime can only null calculation.identity_scope, actual_consumes, "
            "actual_produces and writes, which pyto/viewer/RECORD.md does not declare "
            "nullable and which the reference reader (viewer/adapters.js validate) "
            "refuses -- a document tagged pyto-run-record@1 that is not one."
        )
    # Placement and budget (RECORD.md, "Placement and budget"). The four fields are
    # written together and only when this run has something to say with them -- a
    # parallel run, a budgeted run, or a run a budget stopped. A plain serial
    # unbudgeted run's record is byte for byte the record it was before they
    # existed, which is what "absent means serial, unbudgeted" buys: every consumer
    # that compares a fresh record against a committed one (experiments/students
    # grade.py check 2 drops `duration_ms` and nothing else) keeps working, and a
    # per-Tick wall clock is not silently added to documents that are compared byte
    # for byte ({?} ScheduleFieldsOptional).
    # Effects (RECORD.md, "Effects"). Same rule as the schedule fields, for the
    # same reason: `effects` appears on every invocation of a record whose run had
    # anything to do with effects -- it ran an `oc.` Calculation, or a receipt
    # carries a ledger -- and on none of a record whose run did not, so a pure
    # `fn.` record is byte for byte the record it was before effects existed
    # ({?} EffectsFieldOptional). Inside such a record the field is present for
    # every invocation and empty for every `fn.`, which is the honest reading of
    # "this invocation performed no effect" versus "this runtime records none".
    reports_effects = any(
        getattr(receipt, "effects", ())
        or getattr(receipt.calculation, "address", "").startswith("oc.")
        for receipt in run.receipts.values()
    )
    parallel = bool(getattr(run, "parallel", False))
    budget_ms = getattr(run, "budget_ms", None)
    completed = bool(getattr(run, "completed", True))
    measured_latency = dict(getattr(run, "tick_latency_ms", None) or {})
    reports_schedule = parallel or budget_ms is not None or not completed

    produces_by_id: dict[str, tuple[str, ...]] = {}
    for tick in run.ticks:
        for testimony in tick.calculations:
            produces_by_id[testimony.id] = _produce_addresses(testimony.into)

    if preexisting is None:
        produced_anywhere = {
            address for addresses in produces_by_id.values() for address in addresses
        }
        # This run's own receipts are excluded exactly like the Parts it produced:
        # with observe=True the run wrote one Part per invocation under
        # `px.receipt.<pcr>.<tick>.<id>` (pcr.py:receipt_address), so calling them
        # "preexisting" would report observation as something that preceded the run
        # it observes. Only this run's addresses are excluded; a receipt an earlier
        # run left in the store did preexist this one.
        own_receipts = {
            receipt_address(run.pcr, tick.name, testimony.id)
            for tick in run.ticks
            for testimony in tick.calculations
        }
        preexisting = {
            address
            for address in pxc.addresses()
            if address not in produced_anywhere and address not in own_receipts
        }
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
            receipt = run.receipts[testimony.id]
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
            # adapters.js:244-249 deriveHit, exactly: a `px:` binding this run has
            # not produced yet. `preexisting` is deliberately not consulted -- an
            # address that is preexisting *and* unproduced is already covered, and
            # one this run overwrote and then re-read reused nothing.
            hit = any(address not in produced_so_far for address in px_reads)
            if hit:
                hit_count += 1

            for address in px_reads:
                touch(address)
                if testimony.id not in read_by[address]:
                    read_by[address].append(testimony.id)
            for spelling in fn_reads:
                # pcr.py rewrote a binding on an already-declared Part into its
                # writer's ResultRef, so `fn:<id>` is a read of that writer's `into`
                # Part -- which is why RECORD.md lists fit/score under the split
                # Part's `read_by`. `fn:<id>#<address>` names one produce of a
                # writer that published several.
                for address in _fn_read_addresses(spelling, produces_by_id):
                    touch(address)
                    if testimony.id not in read_by[address]:
                        read_by[address].append(testimony.id)
            for address in receipt.actual_consumes:
                touch(address)
                if testimony.id not in read_by[address]:
                    read_by[address].append(testimony.id)

            for address in receipt.actual_produces:
                touch(address)
                written_by[address] = testimony.id
                produced_so_far.add(address)

            calculation = {
                "address": receipt.calculation.address,
                "implementation_sha256": receipt.calculation.implementation_sha256,
                "identity_scope": receipt.calculation.identity_scope,
            }
            declared_consumes = [f"px:{address}" for address in receipt.declared_consumes]
            actual_consumes = list(receipt.actual_consumes)
            actual_produces = list(receipt.actual_produces)
            writes = [
                {"address": write.address, "kind": write.kind} for write in receipt.writes
            ]
            duration_ms: float | None = receipt.duration_ms
            result_sha256: str | None = receipt.result_sha256
            effects = [effect.as_entry() for effect in getattr(receipt, "effects", ())]
            wall_ms = receipt.duration_ms if wall_ms is None else wall_ms + receipt.duration_ms
            placement = getattr(receipt, "placement", None)

            invocations.append(
                {
                    "id": testimony.id,
                    "calculation": calculation,
                    "inputs": dict(testimony.inputs),
                    "args": dict(testimony.args),
                    "into": (
                        list(testimony.into)
                        if isinstance(testimony.into, tuple)
                        else testimony.into
                    ),
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
                        result_sha256=result_sha256,
                        values_path=_values_path(
                            values_dir, testimony.id, produces_by_id[testimony.id]
                        ),
                    )
                    if testimony.id in run.results
                    else _omitted("the run retained no result for this invocation"),
                    **({"effects": effects} if reports_effects else {}),
                    **(
                        {
                            "placement": (
                                {
                                    "worker": placement.worker,
                                    "started_ms": placement.started_ms,
                                }
                                if placement is not None
                                else None
                            )
                        }
                        if reports_schedule
                        else {}
                    ),
                }
            )
        entry: dict[str, Any] = {"index": index, "name": tick.name, "invocations": invocations}
        if reports_schedule:
            # The Tick's wall time, first start to last finish: measured when the
            # run was parallel (only the run knows when its pool started and
            # stopped), and the sum of its own durations when it was serial --
            # which for a series of Calculations is the same number.
            entry["latency_ms"] = _tick_latency_ms(
                measured_latency.get(tick.name), invocations
            )
        ticks.append(entry)

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

    document: dict[str, Any] = {
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
    if reports_schedule:
        document["parallel"] = parallel
        document["budget"] = {
            "limit_ms": budget_ms,
            "stopped_after_tick": getattr(run, "stopped_after_tick", None),
            "completed": completed,
        }
    return document


def _values_path(
    values_dir: str | None, invocation_id: str, produces: tuple[str, ...]
) -> str | None:
    """Where one invocation's raw array bytes go: `<values_dir>/<address>.bin`.

    Named by the address it published, which is what a reader of the record has in
    hand; an invocation that published several Parts returns one value that is not
    any single address, so that file is named by the invocation instead.
    """
    if values_dir is None:
        return None
    name = produces[0] if len(produces) == 1 else invocation_id
    return os.path.join(values_dir, f"{_safe(name)}.bin")


def _tick_latency_ms(measured: float | None, invocations: list[dict[str, Any]]) -> float | None:
    """One Tick's wall time: what the run measured, else the sum of its durations.

    Null when the runtime recorded no duration for one of the invocations -- a
    partial sum would read as a fast Tick rather than as an unknown one
    (RECORD.md: missing fields are null, never invented).
    """
    if measured is not None:
        return measured
    if not invocations:
        return None
    total = 0.0
    for invocation in invocations:
        duration = invocation["duration_ms"]
        if duration is None:
            return None
        total += duration
    return total


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
    into = invocation["into"]
    into_text = ", ".join(into) if isinstance(into, list) else (into or "-")
    write_text = (
        ", ".join(f"{write['address']} ({write['kind']})" for write in writes)
        if writes
        else into_text
    )
    lines = [
        f"anchor  {record['pcr']} | {tick['name']} | {invocation['id']} | {into_text}",
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
    # `array` reads the same way: its data is a description, and a panel that
    # named the kind and showed neither the dtype nor the digest would be the
    # value-blindness above with an extra step.
    if value["kind"] in ("json", "array"):
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
    try:
        return Image.open(io.BytesIO(base64.b64decode(payload))).convert("RGBA")
    except Exception:
        # RECORD.md:60-61 fixes the prefix, not the payload, so a `png-data-url`
        # whose base64 is truncated or is not a PNG is a legal record -- the JS
        # viewer renders it as a broken <img> and carries on. Drawing must degrade
        # the same way: this invocation keeps its text panel (kind and note are on
        # it) instead of the decoder aborting the run and leaving a half-written
        # ticks/ directory behind.
        return None


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
