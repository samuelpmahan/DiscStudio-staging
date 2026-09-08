# quick_anno Python PCR composition proof

Branch: `task/quick-anno-python-proof`
Base: `b5a6ae040147b488bc44ea94c6303296b2ecde78`

Purpose: test whether local Python can be the cheap investigation/authoring surface while preserving the same compositional PCR shape used by the S0/S1 Mermaid proof. Generic Parts, calculations, queries, graphs, and neon helpers now come from the installed `pyto-lab` distribution; the production snapshot bridge remains ChainSpot-specific.

This is intentionally not a second ChainSpot executor. Python authors a graph; ChainSpot/PxC remains the intended execution owner. `experiments/quick-anno-python/investigation.py` owns only the ChainSpot paths, Node bridge, and output lifecycle.

## Tiny surface

```py
pcr = Pcr("S0")
source = pcr.part("px.source.selectedInput")
decode = pcr.calc("Decode", "fn.s0.decodeFullImage", id="decode", source=source)
bounds = pcr.calc("Crop", "fn.s0.findChromeBounds", id="bounds", image=decode, into="px.source.cropBounds")
pcr.calc("Crop", "fn.s0.applyCrop", id="crop", image=decode, bounds=bounds, into="px.course.canonicalPixels")
```

The same in-memory graph emits:

- `*.pcr.json`: portable PCR-shaped data (`PrincipleComponentRender`, ordered Ticks, Calculations, named bindings, args, optional `into` publication).
- `*.mmd`: Mermaid as a deterministic view of that graph.

The graph preserves the current Mermaid proof's direct-result behavior: once a graph calculation publishes a Part, a later consumption of that Part resolves to the producer calculation result inside the same graph.

## Try it

From repository root:

```sh
# Development checkout supplied outside this repository:
python -m pip install -e /path/to/pyto-lab

# Or the fixed release wheel supplied by the build/integration workflow:
python -m pip install /path/to/pyto_lab-0.1.0-py3-none-any.whl

# Optional legacy import compatibility; declares pyto-lab==0.1.0 and Pillow:
python -m pip install -e packages/quick_anno_py

python3 experiments/quick-anno-python/s0.py
python3 experiments/quick-anno-python/s1.py
python3 -m unittest discover -s packages/quick_anno_py/tests -v
```

Install paths are commands for the current machine, not committed dependency locations. Package metadata pins the distribution and version only: `pyto-lab==0.1.0`.

Generated files land under `experiments/quick-anno-python/generated/` and are deliberately not checked in by this proof.

## What this proves / does not prove

Proves the authoring idea is small: ordinary Python can compose Parts and Calculations and derive both a PCR artifact and a Mermaid render source from one graph.

Does not yet execute through PxC, materialize warm Parts, draw pixel annotations, emit existing PCR YAML byte-for-byte, or plug the generated Mermaid into a browser renderer. Those are the next seams to test only if this authoring surface feels better than JSON/Mermaid-first authoring.

The S0 and S1 examples intentionally mirror `experiments/mermaid-s0-s1/S0.mmd` and `S1.mmd` rather than inventing a new algorithm.
