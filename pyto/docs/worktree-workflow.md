# Working from the extracted seed

## Current topology

The library repository is /mnt/d/pyto. Its main checkout retains the initial provenance checkpoint. Develop the library in /mnt/d/pyto-worktrees/core, branch impl/pyto-core. Reviewed changes are combined in /mnt/d/pyto-worktrees/integration, branch staging/pyto.

The existing ChainSpot repository owns /mnt/d/pyto-worktrees/chainspot on lab/pyto-consumer. The original /mnt/d/Chainspot-python-proto working files stay untouched.

The new consumer source repository is /mnt/d/discstudio-python. Its seed contains workshop code and synthetic statistics, not live user data. /mnt/d/pyto-worktrees/discstudio on impl/pyto-consumer owns the import/execution migration. /mnt/d/pyto-worktrees/cards on feature/layered-customizers owns the separately authorized Single/Battle UI. /mnt/d/pyto-worktrees/discstudio-integration combines them on staging/pyto-customizers.

## Repeatable change cycle

1. Start a bounded worktree from the intended implementation checkpoint. Record exact base SHA and any required working-file snapshot; never implicitly capture unrelated dirty files.
2. Change the shared library once. Keep domain rules in their consumer until demonstrated reuse warrants extraction.
3. During iteration use an editable library install in a development environment. This is deliberately mutable and is not review evidence.
4. Commit the library checkpoint, build a wheel, retain its SHA256 and source SHA. Use a new distribution version when the implementation changes beyond this seed release.
5. Install that fixed wheel in a clean environment. Run library and affected consumer checks without cross-repository sys.path or PYTHONPATH injection.
6. Replace consumer copies with library imports; pin the dependency and retain before/after outputs. Thin compatibility re-exports may preserve old import names, but must expose the exact library objects.
7. Commit each consumer separately. Record library wheel hash, source commits, consumer commits, runtime versions and meaningful output comparisons together.
8. Combine branches in integration worktrees and run the actual user workflow. Update source receipts to cover the implementation that now executes.
9. Preserve previous variants and evidence. Local review pointers stay fixed while implementation branches advance. Publication and main-branch landing remain separate user decisions.

## Starting another LAB

A new LAB can start from a copied domain starter plus a pinned pyto dependency. It inherits P* execution and inspection through imports. Avoid copying the core implementation into every LAB: that would recreate the drift this extraction removes. Broader LAB migration is incremental: preserve a real example, replace one execution path, compare output and checkpoint.

The current Node bridges still execute production ChainSpot stages. They are explicit migration boundaries, not proof of a fully Python LAB. The first useful Python layer already includes named material, executable composition, queries, drawing and two real consumers.

## Evidence and data

Worktree coordination is /mnt/d/pyto-worktrees/WORKTREES.md. Fixed wheels are in artifacts/<source-commit>/; verification is under evidence/. All new work/cache/temp files should use D paths. Original sandbox recipes/events/art archives remain /mnt/d/disc-studio-sandbox. Preview8765 stays on the original implementation; integration preview8781 runs installed packages and its own data.
