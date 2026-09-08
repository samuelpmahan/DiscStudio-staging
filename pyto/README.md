# pyto-lab

`pyto` is a small, dependency-free Python package for composing semantic Parts, calculations, queries, and PCR graphs. It preserves the distinction between executable `PCR` and graph-authoring `Pcr`.

```python
from pyto import Calculation, Part, PCR, PxC

value = Part("px.value")
double = Calculation("fn.double", lambda args: args["value"] * 2)
pxc = PxC()
pxc.set(value, 21)
pcr = PCR("demo")
pcr.calc("main", double, id="double", value=value)
print(pcr.run(pxc).results["double"])  # 42
```

Install locally with `python -m pip install .`. For development with the optional drawing helpers, use `python -m pip install -e '/mnt/d/pyto-worktrees/core[drawing]'`. A review install can use `python -m pip install /path/to/pyto_lab-0.1.0-py3-none-any.whl`. The core package has no runtime dependencies.

Run the executable example with `python examples/basic.py` from the repository root. The adapted source checks can be run without pytest with `PYTHONPATH=src python -c "import sys; sys.path.insert(0, 'tests'); import test_first_class as t; t.test_pxc_is_fail_loud_and_pql_is_composable(); t.test_pcr_preserves_direct_result_and_publication_semantics(); t.test_duplicate_writer_rejected(); print('first-class tests: 3 passed')"`.


## Extraction and integration

The six library modules were extracted byte-for-byte from the source seed recorded in docs/seed-manifest.json. ChainSpot-specific StageInvestigation remains in the ChainSpot experiment. The old ChainSpot package becomes compatibility re-exports, so there is one executing implementation.

The first fixed library wheel was built from commit15e3467. Review artifacts live under /mnt/d/pyto-worktrees/artifacts/15e3467. A clean installation was verified with Python isolated mode and no Pillow, and a separate clean consumer environment exercises real HTTP and ChainSpot snapshot callers.

The reusable HTTP parity check is `scripts/verify_disc_consumer.py`. Run it with an installed pyto package, --consumer pointing at the DiscStudio source worktree, --art-library pointing at retained fixtures, and --output pointing at the evidence file. It checks all36 retained SVGs, actual calculation testimony, hashes of executing sources and absence of render persistence.

Development can use editable installs. Review evidence always records a fixed wheel hash and exact consumer commits. Do not claim the full LAB engine is ported: existing ChainSpot production stages still execute through the Node bridge.
