# Library candidates from awesome-python

Source: https://github.com/vinta/awesome-python (user-supplied 2026-09-08 as "some of these may be useful").
Status: candidate pool only. Nothing here is adopted. The pyto core stays dependency-free until a
runnable consumer demonstrates the need (docs/PYTHON-LAB-STEWARDSHIP.md), and the research entrypoint
asks for "the smallest conventional implementation that provides a fair comparison" — several
candidates are useful precisely as that comparison baseline, not as dependencies.

| Need in the workshop | Candidates | Role | Prohibition check |
|---|---|---|---|
| Fair comparison: "a function registry, cache, or workflow engine may provide a useful comparison after the semantics are understood" | joblib (Memory), cachetools, diskcache, dask (delayed graph), prefect, dagster, doit, luigi (not listed) | Comparison baseline for PxC memoization and PCR composition; measure saved implementation / computation against the same fixture | Comparison only; do not migrate pyto onto them |
| Table projection of PxC ("a Pandas projection would provide another interface") | pandas, polars, duckdb | Projection experiment: what survives a table projection and a subsequent use of its results in PxC | Projection is an interface, not the substrate |
| Retained program schema and replay (stewardship queue item 1) | jsonschema, msgspec, pydantic, tomllib/pyyaml | Validate the declarative retained-program document; JSON stays the wire format for JS parity | No pickled lambdas; no executable code in the retained data |
| Content addressing, hashes, canonical bytes | hashlib (stdlib), xxhash (not listed) | Content-addressed Part keys like ChainSpot matrix/materials.ts | stdlib first |
| Property-based tests for fail-loud rules and replay round trips | hypothesis | Generate compositions; assert replay == original testimony, duplicate-writer rejection, PQL cardinality | Test-only dependency |
| Dependency and graph questions ("ordinary traversal ... do not silently turn PQL into a graph-mining framework") | networkx, pygraphviz | Traversal and rendering of PcrRun testimony; SUBDUE-style substructure counting on the composition graph in the comparison experiment | Experiment-scoped, not a PQL feature |
| Timing and profiling in testimony (ablation runs need per-run timing) | time.perf_counter (stdlib), pyinstrument, py-spy | Record wall time per invocation; profile the neon materializers | stdlib first |
| Comparison of retained runs (queue item 3) | deepdiff (not listed), difflib (stdlib) | Explain what changed: code, bindings, or produced values | Keep the first comparison specific to Card/art behavior |
| Evidence and reports | rich, structlog, tqdm | Human-readable evidence tables in the terminal; JSON stays the retained form | Optional |
| Ablation combinatorics | itertools (stdlib), more-itertools | Group selection over 15 features without enumerating 32,768 subsets | stdlib first |
| Image work already in neon.py | pillow (present), scikit-image, numpy | Only when a CV consumer returns; browser budget is separate | Do not import into the core |
| Static checks on the library | ruff, mypy or pyright | One-command lint and type check on pyto/src | Tooling only |

Recommended use in the week: one scout stage compares joblib.Memory, dask.delayed and a plain dict
registry against the same synthetic ablation fixture that the pyto experiment runs, reporting lines
of glue, recomputation avoided, and what each cannot express (testimony, publication into named
Parts, replay from declarative data). hypothesis and jsonschema are the only candidates proposed as
actual (test-time) dependencies, and only if the replay seam lands.
