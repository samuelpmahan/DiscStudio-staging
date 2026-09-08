# DiscStudio agent contract

Work through the existing PxC/PQL integration. Do not create a competing state store, customizer field whitelist, preview renderer or export renderer. Ordinary implementation helpers belong inside the existing Calculations.

Before editing, inspect `src/domain.js`, `src/runtime.js`, `src/presentation.js`, `src/constraints.js`, the relevant tests, and `.neat/items/DS-STUDIO-02.json`. Reuse existing fields, Parts and Calculations. New domain types declare their fields/relationships once; appearance is independent from source objects. A saved preset has bindings, not copied specimen values.

For each reviewable change, update the addressed neat requirements and `src/review-data.js` together. Give it a concrete review route, how to inspect it, and an honest verification result. Keep verification and acceptance separate. Never check review boxes or record human acceptance on Sam's behalf. Downloaded comments contain requirement IDs and exact build context; address the specific item rather than rewriting the whole product.

Run `npm test`, `npm run build`, and the normal Playwright browser checks when available. Render and inspect changed surfaces. Report actual source commit, tests run, produced Parts, reused material, screenshots/exports and limitations. An embedded browser run with a storage double is not real browser reload verification. A source snapshot is not a deployed build.

Preserve optional flight numbers, specimen identity, shared Bag references, authored state separation, and original source photos in the user's possession. Inspector selection must not alter export semantics. Do not silently omit missing objects, infer a winner, turn an export into audience reach, or transmit local data.

No core renaming, new DSL, backend, CV integration or architecture migration unless specifically assigned. A new design should reuse existing elements and bindings; a genuinely new visual primitive should be one reusable Calculation/component, not another frontend fork.
