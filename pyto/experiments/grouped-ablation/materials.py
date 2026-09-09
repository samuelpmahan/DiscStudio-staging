"""Content-addressed materials, ported experiment-locally from ChainSpot's LAB.

Reference: pyto/reference/lab/chainspot-matrix/matrix/materials.ts:263-317
(`createMatrixMaterials` and its `MatrixMaterialCounters`) and the accompanying
`matrixMaterials.test.ts`. Nothing here moves into pyto/src -- see
pyto/questions.md; the Day 3 plan (research/ULTRACODE-WEEK.md, Reframing 2 and
Reframing 3) asks for this mechanism "ported experiment-locally", and the {?}
PromotionScope judgment keeps every experiment-scoped primitive there until the
owner asks for it beyond its originating uses.

``canonical(value)`` is materials.ts's ``canonical()`` (lines 158-163) transcribed
line for line: a scalar goes through ``json.dumps``, a list/tuple is the
element-wise canonical form joined with commas inside brackets, and a dict is its
keys sorted and each ``"key":canonical(value)`` pair joined with commas inside
braces -- so two Python dicts built in different insertion order, or a Python
dict and the equivalent JS object, canonicalize to the same bytes and therefore
hash to the same key (test_materials.py::CanonicalKeyStability).

``sha(text)`` is sha256 hex, matching materials.ts's ``sha()``.

``MaterialsStore`` is the durable, per-user backend Reframing 3 asks for ("A
Part produced in one process or project can be verified and reused in
another"): a plain-JSON-file store rooted at ``PYTO_MATERIALS_DIR`` or
``~/.pyto/materials`` (``default_root()`` reads the environment variable at call
time, not at import time, so a test or a subprocess can point it at a scratch
directory). The directory is created on demand -- nothing is written at
construction, only inside ``save()``'s first write -- and its counters
(``requests``, ``hits``, ``misses``, ``writes``) accumulate across every
``material()`` call that shares the instance, the same four fields
``MatrixMaterialCounters`` carries (materials.ts's ``profileHits`` /
``profileMisses`` / ``profileWrites`` are ChainSpot's separate pose-read tier;
this port has no counterpart to it and does not add one).

``material(pxc, *, revision, source, calculation, args)`` is
``createMatrixMaterials``'s key/hit/miss/write sequence (materials.ts:296-317),
generalized from one CV material to any registered ``pyto.Calculation``:

    key = sha(canonical({"revision": revision, "source": source, "args": args}))
    address = f"material.{key}"

    1. ``pxc.has(address)``     -> in-PxC hit:  ``return pxc.get(address)``
    2. ``store.has_value(key)`` -> disk hit:    load, ``pxc.set(address, value)``, return
    3. otherwise                -> miss:        ``value = pxc.call(calculation, args)``;
                                                 ``pxc.set(address, value)``; ``store.save(key, value)``

``revision`` is the key's hook into calculation identity -- the caller supplies
it rather than this module inferring it, so the choice of what counts as a
revision stays visible at the call site. Day 2's ``implementation_sha256``
(``pyto.pcr.FrozenCalculation``, ``pcr.py:90-93``) is the candidate the plan
names for it ({?} CacheInvalidation, research/ULTRACODE-WEEK.md Reframing 2: "the
key's `revision` component is a calculation identity ... its scope excludes
helpers and assets"); ``run_cached.py`` uses exactly that field, read off the
'split' invocation's own receipt, as the revision for ``fn.ablation.split``.

A value that does not serialize as JSON is never written as the cached value --
no pickle, no marshal, docs/PYTHON-LAB-STEWARDSHIP.md:39. ``MaterialsStore.save``
falls back to a digest+ref sidecar (a ``repr()`` text file plus a small JSON
pointer to it) instead, and ``has_value()`` is False for a sidecar-only key, so a
non-JSON result is recomputed -- and its sidecar rewritten -- on every call
rather than silently pretending to be cached (test_materials.py::
NonJSONValueSidecar).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pyto import Calculation, PxC

DEFAULT_MATERIALS_DIR = "~/.pyto/materials"
_ENV_VAR = "PYTO_MATERIALS_DIR"


def canonical(value: Any) -> str:
    """Key-sorted JSON text; the same shape regardless of dict insertion order.

    Transcribed from materials.ts:158-163. Only JSON-safe scalars, lists/tuples
    and dicts (with str-able keys) are supported, matching the TS source's
    ``Record<string, unknown>`` assumption -- object keys are always strings.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return json.dumps(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(canonical(item) for item in value) + "]"
    if isinstance(value, dict):
        pairs = (f"{json.dumps(str(key))}:{canonical(value[key])}" for key in sorted(value, key=str))
        return "{" + ",".join(pairs) + "}"
    raise TypeError(f"canonical(): unsupported type {type(value).__name__!r}")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def default_root() -> Path:
    """``PYTO_MATERIALS_DIR`` if set, else ``~/.pyto/materials``.

    Read at call time (not cached at import time) so a test, or a fresh
    ``python3 -I`` process sharing a temp-dir store, can point this elsewhere by
    setting the environment variable before constructing a ``MaterialsStore``.
    Never creates the directory -- see ``MaterialsStore``, "created on demand".
    """
    configured = os.environ.get(_ENV_VAR)
    return Path(configured) if configured else Path(os.path.expanduser(DEFAULT_MATERIALS_DIR))


def _fresh_counters() -> dict[str, int]:
    return {"requests": 0, "hits": 0, "misses": 0, "writes": 0}


@dataclass
class MaterialsStore:
    """Durable, per-user disk backend for ``material()``.

    ``root`` defaults to ``default_root()`` and is never created here: the
    directory need not exist at construction, and the first thing that creates
    it is ``save()``'s own ``mkdir(parents=True, exist_ok=True)``. Two
    ``MaterialsStore()`` instances built against the same ``root`` (a fresh
    process included, via ``PYTO_MATERIALS_DIR``) see each other's writes; two
    instances against different roots never collide because the key is only a
    filename, not a namespace.

    ``counters`` accumulate across every ``material()`` call sharing this
    instance -- the shape matches ``MatrixMaterialCounters`` exactly:
    ``requests``, ``hits``, ``misses``, ``writes``.
    """

    root: Path = field(default_factory=default_root)
    counters: dict[str, int] = field(default_factory=_fresh_counters)

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    def _value_path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def _sidecar_path(self, key: str) -> Path:
        return self.root / f"{key}.sidecar.json"

    def has_value(self, key: str) -> bool:
        """True only when a *value* was persisted for this key.

        A sidecar-only key (the value was not JSON-serializable) is never a
        disk hit: the value itself was never written, only a digest and a
        `repr()` reference, so there is nothing here to load back as the
        material.
        """
        return self._value_path(key).is_file()

    def load_value(self, key: str) -> Any:
        with self._value_path(key).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, key: str, value: Any) -> str:
        """Persist `value` as JSON when it serializes; otherwise a digest+ref
        sidecar, never the value itself (docs/PYTHON-LAB-STEWARDSHIP.md:39: no
        retained data claims to contain executable code, and a ``repr()`` text
        file is data, not a pickle). Returns ``"value"`` or ``"sidecar"``.
        Idempotent -- safe to call on every miss.
        """
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            payload = json.dumps(value, sort_keys=True)
        except (TypeError, ValueError):
            ref_name = f"{key}.ref.txt"
            digest = hashlib.sha256(repr(value).encode("utf-8")).hexdigest()
            with (self.root / ref_name).open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(repr(value))
                handle.write("\n")
            with self._sidecar_path(key).open("w", encoding="utf-8", newline="\n") as handle:
                json.dump({"digest": digest, "ref": ref_name, "type": type(value).__name__}, handle, sort_keys=True, indent=2)
                handle.write("\n")
            return "sidecar"
        with self._value_path(key).open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.write("\n")
        return "value"


def material_key(*, revision: str, source: Any, args: Any) -> str:
    """The content-addressed key `material()` uses -- exposed so a caller (or a
    fresh-process test) can recompute it without a PxC or a Calculation."""
    return sha(canonical({"revision": revision, "source": source, "args": args}))


def material(
    pxc: PxC,
    *,
    revision: str,
    source: Any,
    calculation: Calculation[Any, Any],
    args: Any,
    store: MaterialsStore | None = None,
) -> Any:
    """``createMatrixMaterials``'s hit/miss/write sequence, generalized to any
    ``Calculation``. See the module docstring for the full three-step rule.

    `store` defaults to a fresh `MaterialsStore()` (so a bare call still works
    against the per-user default root); pass one explicitly to share counters
    and a disk root across multiple PxCs or processes, as `run_cached.py` does.
    """
    store = MaterialsStore() if store is None else store
    key = material_key(revision=revision, source=source, args=args)
    address = f"material.{key}"
    store.counters["requests"] += 1

    if pxc.has(address):
        store.counters["hits"] += 1
        return pxc.get(address)

    if store.has_value(key):
        store.counters["hits"] += 1
        value = store.load_value(key)
        pxc.set(address, value)
        return value

    store.counters["misses"] += 1
    value = pxc.call(calculation, args)
    pxc.set(address, value)
    store.save(key, value)
    store.counters["writes"] += 1
    return value
