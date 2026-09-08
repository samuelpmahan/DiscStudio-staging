# Tidy delivery-freeze scout

Scope: read-only inspection of `/mnt/d/disc-studio-ws/tidy` README, `docs/TIDY.md`, `tidy`, and focused tests. No command was run against a target repository; no install, server, backup, or mutation was performed.

## Observed behavior

- Tidy describes itself as a working-tree lineage guard. Git owns history. It explicitly does not manage branches, decide `clean/` contents, or coordinate work ([README.md](/mnt/d/disc-studio-ws/tidy/README.md:3), [README.md](/mnt/d/disc-studio-ws/tidy/README.md:51)).
- `check` reads `.tidy/manifest.json` and validates JSON, `schemaVersion === 1`, type names/specs, semver `version`, non-empty test commands, and optional safe relative `root`/`clean`/`experiments` paths ([tidy](/mnt/d/disc-studio-ws/tidy/tidy:19), [tidy](/mnt/d/disc-studio-ws/tidy/tidy:28)). It does not inspect Git state or artifacts.
- `promote TYPE EXPERIMENT PATH [--replace]` resolves one source file under the configured experiment directory and copies it to the matching `clean` path. It blocks path traversal and symlink escapes, refuses an existing destination without `--replace`, leaves the experiment source in place, runs the configured tests, and leaves the copied destination when tests fail ([README.md](/mnt/d/disc-studio-ws/tidy/README.md:97), [tidy](/mnt/d/disc-studio-ws/tidy/tidy:319)). Directory/subtree promotion is explicitly deferred ([README.md](/mnt/d/disc-studio-ws/tidy/README.md:106)).
- `up -v TYPE:TARGET_VERSION` accepts only one legal patch/minor/major successor, requires the lineage `clean` directory to exist, runs configured tests, and then updates only the manifest version. A failed test blocks by default; an explicit patch-only bypass exists ([docs/TIDY.md](/mnt/d/disc-studio-ws/tidy/docs/TIDY.md:16), [tidy](/mnt/d/disc-studio-ws/tidy/tidy:255)).
- The optional pre-commit hook runs only `./tidy check`; it does not inspect staged files or call `up` ([README.md](/mnt/d/disc-studio-ws/tidy/README.md:61), [docs/TIDY.md](/mnt/d/disc-studio-ws/tidy/docs/TIDY.md:90)).
- Manifest writes use a same-directory temporary filename followed by `renameSync` ([tidy](/mnt/d/disc-studio-ws/tidy/tidy:194)). This is an implementation-level replace pattern; there is no lock, fsync, journal, stale-temp cleanup, or recovery command in the inspected surface.

## Exact questions

| Question | Finding | Classification |
|---|---|---|
| What freezes today? | Nothing freezes a Delivery or working tree. `promote` copies one named file; `up` records a version after checks/tests. | Observed |
| Committed state? | No Git commands or commit/base inspection exist. | Observed gap |
| Uncommitted state? | No Git status/diff/index inspection exists. | Observed gap |
| Untracked state? | No untracked-file enumeration exists. | Observed gap |
| Binary files? | `copyFileSync` can copy a file byte-for-byte, but there is no freeze inventory or binary-specific metadata/validation. | Observed + narrow inference |
| Renames/deletions? | No tree diff, rename detection, deletion record, or subtree promotion exists. | Observed gap |
| Source base SHA? | Not captured. | Observed gap |
| Manifest/source hashes? | The Tidy manifest stores schema/types/version/tests/relative paths only; no content hashes or Git SHA. | Observed |
| Atomic write/recovery? | Manifest replacement is temp-write then rename. No durability or crash-recovery protocol is present. | Observed + limitation |
| Immutable Delivery manifest pointing at existing outputs? | No `Delivery` type, output reference, immutable manifest, or pointer/check command exists. Any such design would be new behavior. | Observed gap |
| `.neat` / `.neat.bak`? | No `.neat` or backup/archive command or documentation appears in the inspected tidy surface. The requested `.neat` patch/doc retention policy is therefore external to current Tidy. | Observed gap |

## Implications for the proposed design

The current primitive can serve as a lineage/version gate and single-file promotion step, but it cannot establish a reproducible Delivery freeze. A freeze would need an explicit inventory boundary (including Git base and working-tree additions/deletions), deterministic per-path metadata/content hashes, treatment for binary files and renames, and a Delivery manifest whose references and hashes are immutable. The existing temp-plus-rename write is useful for replacing one manifest file, but does not by itself provide crash recovery or multi-file atomicity.

No Qustomize or Pythagorean marker was encountered in the inspected files, so those skills were not opened.
