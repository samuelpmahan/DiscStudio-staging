"""What a generation of the owner's evolutionary art loop pays for its record.

The shape is his, not a microbenchmark's. One generation is 32 genomes; each one
is rendered, and a render is the thing this bench is about:

  - today a render is a **flat list of 196,608 integers** (256x256x3 rgb), which
    is what the observed generation in exp/evo-pxc returns, and
  - on the mac the loop moves to numpy end to end, so a render becomes a
    **(256, 256, 3) uint8 ndarray**,

both of them through an observed PCR, which is the run that reported 8.6 s to
materialize its record and 10.4 s to write it, with 3.8 s of `_result_sha256`
inside the generation itself.

    .venv/bin/python pyto/scripts/bench_record.py
    .venv/bin/python pyto/scripts/bench_record.py --genomes 4    # a quicker look
    .venv/bin/python pyto/scripts/bench_record.py --images       # and 1024x1024 PIL renders

It prints the seconds and the bytes for each kind of render, and the kinds the
record gave the values: a change that makes materializing cheap by dropping what
the record says is not the change we want, and the kinds line is the evidence
that it still says it.

No assertion and no threshold: this is evidence to read and to commit beside a
packet, never a test (a timing test cost a landing once).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
from collections import Counter
from time import perf_counter

import pyto.pcr as pcr
from pyto import Calculation, PCR, Part, PxC
from pyto.materialize import run_record, write_record

CANVAS = (256, 256, 3)
POINTS = CANVAS[0] * CANVAS[1] * CANVAS[2]  # 196608
IMAGE_SIZE = (1024, 1024)


def rgb_list(args):
    """The render as it is today: a flat list of rgb integers."""
    generator = random.Random(args["seed"])
    return [generator.randrange(256) for _ in range(args["points"])]


def rgb_array(args):
    """The render as it will be: the same numbers as a uint8 ndarray."""
    import numpy

    generator = numpy.random.default_rng(args["seed"])
    return generator.integers(0, 256, size=args["shape"], dtype="uint8")


def rgb_image(args):
    """A 1024x1024 RGB PIL image, the render of the first brief."""
    from PIL import Image

    pixels = random.Random(args["seed"]).randbytes(IMAGE_SIZE[0] * IMAGE_SIZE[1] * 3)
    return Image.frombytes("RGB", IMAGE_SIZE, pixels)


LIST = Calculation("fn.evo.render_list", rgb_list)
ARRAY = Calculation("fn.evo.render_array", rgb_array)
IMAGE = Calculation("fn.evo.render_image", rgb_image)


def build(kind: str, genomes: int, points: int) -> tuple[PCR, PxC, set[str]]:
    pcr_program = PCR(f"generation-{kind}")
    pxc = PxC()
    for index in range(genomes):
        suffix = f"{index + 1:02}"
        if kind == "list":
            args = {"seed": index, "points": points}
            calculation = LIST
        elif kind == "array":
            args = {"seed": index, "shape": list(CANVAS)}
            calculation = ARRAY
        else:
            args = {"seed": index}
            calculation = IMAGE
        pcr_program.calc(
            "render",
            calculation,
            id=f"render_{suffix}",
            into=Part(f"px.evo.render.{suffix}"),
            args=args,
        )
    return pcr_program, pxc, set(pxc.addresses())


def _safe(label: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in label)


def _directory_bytes(path: str) -> int:
    if not os.path.isdir(path):
        return 0
    return sum(os.path.getsize(os.path.join(path, name)) for name in os.listdir(path))


def one(
    kind: str,
    genomes: int,
    points: int,
    out: str,
    values: bool,
    value_cap_bytes: int,
    array_cap: int,
) -> None:
    program, pxc, preexisting = build(kind, genomes, points)

    # The receipt's own digesting, measured where it happens: `_result_sha256` is
    # called once per invocation and once per published address, inside the run.
    spent = [0.0, 0]
    original = pcr._result_sha256

    def timed(value):
        started = perf_counter()
        try:
            return original(value)
        finally:
            spent[0] += perf_counter() - started
            spent[1] += 1

    pcr._result_sha256 = timed
    try:
        started = perf_counter()
        run = program.run(pxc, observe=True)
        run_s = perf_counter() - started
    finally:
        pcr._result_sha256 = original

    label = kind
    record_path = os.path.join(out, f"{_safe(label)}-record.json")
    values_dir = os.path.join(out, f"{_safe(label)}-record.values") if values else None

    # Without a values directory this is the call `run_record` has always had, so
    # `--no-values` is what you run against an older pyto to get the before.
    keywords = {
        "preexisting": preexisting,
        "value_cap_bytes": value_cap_bytes,
        "array_cap": array_cap,
    }
    if values_dir is not None:
        keywords["values_dir"] = values_dir
    started = perf_counter()
    record = run_record(run, pxc, **keywords)
    materialize_s = perf_counter() - started

    started = perf_counter()
    write_record(record, record_path)
    write_s = perf_counter() - started

    kinds = Counter(
        invocation["value"]["kind"]
        for tick in record["ticks"]
        for invocation in tick["invocations"]
    )
    print(f"== {genomes} renders as {label}")
    print(f"   run           {run_s:7.2f} s   (the generation, receipts and all)")
    print(f"   of which      {spent[0]:7.2f} s   in _result_sha256, {spent[1]} calls")
    print(f"   materialize   {materialize_s:7.2f} s   run_record")
    print(f"   write         {write_s:7.2f} s   write_record")
    print(f"   record+write  {materialize_s + write_s:7.2f} s   what the record costs on top")
    print(f"   record        {os.path.getsize(record_path) / 1048576:7.1f} MiB")
    if values_dir:
        print(f"   values        {_directory_bytes(values_dir) / 1048576:7.1f} MiB beside it")
    print(f"   value kinds   {json.dumps(dict(sorted(kinds.items())))}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--genomes", type=int, default=32)
    parser.add_argument("--points", type=int, default=POINTS)
    parser.add_argument("--images", action="store_true", help="also the 1024x1024 PIL render")
    parser.add_argument("--out", default=None, help="where the records go (default: a temp dir)")
    parser.add_argument(
        "--no-values", action="store_true", help="do not write array buffers beside the record"
    )
    # The caps the owner's own generation passed to run_record: nothing was
    # truncated and nothing was dropped, which is why its record was 109 MiB.
    # Run with the defaults (256 KB, 200 entries) to see the other end of it.
    parser.add_argument("--value-cap", type=int, default=16000000)
    parser.add_argument("--array-cap", type=int, default=250000)
    options = parser.parse_args(argv)

    out = options.out or tempfile.mkdtemp(prefix="bench-record-")
    os.makedirs(out, exist_ok=True)
    kinds = ["list"]
    try:
        import numpy  # noqa: F401

        kinds.append("array")
    except ImportError:
        print("no numpy here: skipping the array render", file=sys.stderr)
    if options.images:
        try:
            import PIL  # noqa: F401

            kinds.append("image")
        except ImportError:
            print("no Pillow here: skipping the image render", file=sys.stderr)

    print(f"genomes        {options.genomes}")
    print(f"points         {options.points} per render (list), {CANVAS} uint8 (array)")
    print(f"caps           {options.value_cap} bytes, {options.array_cap} entries")
    print(f"out            {out}")
    for kind in kinds:
        one(
            kind,
            options.genomes,
            options.points,
            out,
            not options.no_values,
            options.value_cap,
            options.array_cap,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
