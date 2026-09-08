# DiscStudio Python consumer

This worktree consumes the independently packaged `pyto-lab==0.1.0`. The original sandbox, saved user data and all art variants remain under `/mnt/d/disc-studio-sandbox`. This checkout uses isolated data.

## Install and run

For fixed review, install the recorded library wheel and this consumer in a Python environment with pip and setuptools:

```sh
python -m pip install /mnt/d/pyto-worktrees/artifacts/15e3467/pyto_lab-0.1.0-py3-none-any.whl
python -m pip install --no-build-isolation --no-deps .
python app.py --root . --port 8781
```

For library development, install `/mnt/d/pyto-worktrees/core` in editable mode instead of the wheel. Re-run the consumer checks when changing the library. Do not install an unrelated same-name package from a public index.

```sh
python -m pip install -e /mnt/d/pyto-worktrees/core
```

`index.html` is served from the explicit root; it is not bundled into the Python distribution. The installed Python modules provide backend code; the working tree supplies the preview page and data location.

## Real library boundary

`POST /api/art` creates named input/output Parts and runs `fn.discArt.render` through Pyto PCR. The disc painter remains domain code in `paint_components.py`. Original SVG bytes and receipt fields are preserved. Additional composition evidence records actual installed Pyto version, core/PCR module source hashes, adapter source hash and executed calculation testimony. These hashes cover the named files, not every transitive runtime dependency.

The synthetic statistics experiment uses installed `pyto` directly, without cross-repository sys.path injection. Its fixtures are demonstrations, not real owner or shot-performance evidence.

## Checks

```sh
python -m unittest test_sandbox test_art_backend -v
python experiments/disc-stats/test_stats.py
python experiments/disc-stats/run_experiment.py
```

Use a D-drive TMPDIR for temporary evidence. Root integration verification compares the actual HTTP output with all 36 retained SVGs; command and results are recorded in `/mnt/d/pyto-worktrees/evidence`. No tests write to the original user data.

## Retention

The seed manifest records the original source. Recipe saves remain immutable, event writes append, and rendering itself does not persist a recipe or event. Existing live 8765 stays on the original source until separately applied. This work is local and has no configured remote publication.

## Layered customizers

The shared Disc Customizer feeds the Single card and the first slot of a neutral Battle card. The second slot stays empty until a saved presentation is selected. Its name, note, flight values, artwork settings and physical-disc identity remain a retained snapshot when the active trial changes.

Single offers a draggable **Free arrangement** and fixed **Artwork above numbers**. Battle offers **Side by side** and **Stacked**. Each card independently shows or hides names, notes and flight numbers. Layout choices change rendered positions and dimensions; they do not change the other card's layout.

Schema 3 recipes retain the active disc fields, a `physicalDiscId`, a separate `presentationId`, and `cards.single`/`cards.battle` with `type`, `layout`, `details` and `discRecipeIds`. A `presentations` map embeds the referenced disc presentations, with no nested card recipes. The browser accepts at most two presentations and 64KB of input. `discId` remains a compatibility alias of `physicalDiscId`; conflicting aliases are rejected. Legacy physical IDs remain valid strings, including spaces. Recipes missing card settings get a single active presentation and an empty second Battle slot.

Save and Keep persist an immutable snapshot and fork the active presentation identity while retaining the same physical identity. Loading or applying a recipe opens a new editable presentation trial; embedded saved participants remain fixed. Keep also retains both card views beside the trial. Save telemetry includes `savedRecipe` and `savedPresentationId`, so edits made during the request cannot obscure the exact persisted version.

Both active and retained participant artwork use `/api/art` at 42/96/220px. A bounded in-tab cache uses the complete artwork inputs, and snapshot receipts are attributed to each presentation's own inputs. Imported receipts are not reused as fresh execution evidence. Replay renders the embedded artwork settings again. Recipe shape validation happens in the browser; the existing backend still stores JSON unchanged.

This slice has two participants, two layouts per card and one details toggle per card. It adds no winner, score or shot-tracking behavior, and does not change the Python renderer or package dependencies.

### Browser verification

Run an isolated preview backend with its own D-drive root/data, then:

```sh
CARDS_URL=http://127.0.0.1:8782 \
CARDS_EVIDENCE=/mnt/d/pyto-worktrees/evidence/cards \
PLAYWRIGHT_BROWSERS_PATH=/tmp/discstudio-browser-cache \
LD_LIBRARY_PATH=/tmp/discstudio-browser-libs/extracted/usr/lib/x86_64-linux-gnu \
TMPDIR=/mnt/d/pyto-worktrees/evidence/cards/tmp \
/mnt/d/disc-studio-ws/.runtime/node-v22.23.2-linux-x64/bin/node tests/layered-customizers.cjs
```

The test uses the existing Playwright package at `/tmp/discstudio-browser/node_modules/playwright` (override with `PLAYWRIGHT_MODULE`). Evidence includes actual layout screenshots, immutable saved/replayed recipes, exact per-presentation receipt-input hashes, browser assertions and a 390px overflow check. It creates only test variants/events in the selected preview server's data root. Do not point it at the live user server.
