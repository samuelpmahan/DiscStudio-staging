from pathlib import Path

from pyto import Pcr


pcr = Pcr("S0")
source = pcr.part("px.source.selectedInput")

decode = pcr.calc(
    "Decode",
    "fn.s0.decodeFullImage",
    id="decode",
    source=source,
)

bounds = pcr.calc(
    "Crop",
    "fn.s0.findChromeBounds",
    id="bounds",
    image=decode,
    into="px.source.cropBounds",
)

pcr.calc(
    "Crop",
    "fn.s0.applyCrop",
    id="crop",
    image=decode,
    bounds=bounds,
    into="px.course.canonicalPixels",
)

OUT = Path(__file__).with_name("generated")
OUT.mkdir(exist_ok=True)
(OUT / "S0.pcr.json").write_text(pcr.to_pcr_json())
(OUT / "S0.mmd").write_text(pcr.to_mermaid())

print(f"wrote {OUT / 'S0.pcr.json'}")
print(f"wrote {OUT / 'S0.mmd'}")
