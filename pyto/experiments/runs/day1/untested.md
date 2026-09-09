# Day 1 completeness critic: rules from the plan's 'NOT verified by any test' list vs the retained tests

Source list: research/ULTRACODE-WEEK.md:46 (pcr.py:33-56, 86-96, 109-123, 151-164; core.py:18-19, 33-34, 58-71; pql.py:55-73).
Compared against: tests/test_semantics.py (31 tests) and tests/test_first_class.py (9 tests) as of 9435f15 + working tree; test line numbers cite the working tree.
Verdict file: verdicts/completeness.json. Rules still untested are listed as MISSING below and are kept, not dropped.

Rules: 34; covered: 30; MISSING: 4.

## MISSING (no test asserts the rule)

- MISSING pcr.py:45: Tick.calc coerces a str `into` to Part when called directly: pcr.tick(name).calc(..., into='px.x'). Evidence: no test passes a str into through Tick.calc: tests/test_semantics.py:401 uses the default into=None and :417 passes the Part OUT; PCR.calc pre-coerces at pcr.py:118 and hands the Part to Tick.calc at pcr.py:128, so every PCR-level str-into test (:328, :337, :356-357, :510-512, :529-530) stops at pcr.py:118 and never reaches pcr.py:45.
- MISSING pcr.py:52: Tick.calc stores a copy of args (dict(args or {})): args=None becomes {} and the caller's mapping is not aliased by the Invocation. Evidence: testimony args is asserted only for a supplied mapping (tests/test_semantics.py:441 `testimony.args == {'value': 'from-args'}`); no test asserts `args == {}` on an invocation declared without args, and no test mutates the caller's args mapping after declaration to show the Invocation (and pcr.py:171 testimony) is unaffected.
- MISSING pcr.py:89: _ids is per PCR: two PCRs may declare the same invocation id without error. Evidence: tests/test_semantics.py:538-557 is the only two-PCR test and uses distinct ids ('w' and 'r'); no test declares one id in two PCRs (and no test shows that a PCR.calc rejected by Tick.calc at pcr.py:43 leaves _ids untouched, pcr.py:132).
- MISSING pql.py:73: optional() returns the single match's value when exactly one Part matches (`matches[0].value if matches`). Evidence: optional() is called only with zero matches (tests/test_semantics.py:248) and two matches (:267); no test asserts the one-match return value, so a mutant `return None` at pql.py:73 would survive (one() at :143 of test_first_class.py covers the sibling path only).

## Covered

| target | rule | test(s) |
| --- | --- | --- |
| pcr.py:43-44 | Tick.calc rejects a duplicate id within the same tick | tests/test_semantics.py:383 PCRDeclarationRulesTest.test_tick_calc_rejects_duplicate_id_within_tick (docstring 'pcr.py:43-44'; killed by `if False:` at pcr.py:43, mutation-kill.md) |
| pcr.py:46 | Tick.calc wraps any binding source in Binding without a type check (silent; discriminated only at run, pcr.py:147-151) | tests/test_semantics.py:367 PCRDeclarationRulesTest.test_non_part_binding_source_fails_at_run (docstring cites 'Tick.calc (pcr.py:46)'; critic gap 13) |
| pcr.py:47-55 | Tick.calc appends the Invocation in declaration order, so execution order inside a tick is declaration order | tests/test_semantics.py:443 PCRRunRulesTest.test_result_ref_to_unavailable_id_fails_only_at_run (a producer declared later in the same tick is 'unavailable'); tests/test_first_class.py:194-202 (cards tick lists single-card before battle-card) |
| pcr.py:53 | into may be None: run publishes nothing for that invocation (pcr.py:163) | tests/test_semantics.py:393-406 test_tick_calc_bypasses_pcr_duplicate_id_rule (Tick.calc without into; run completes and results['w1'] is read), :443-457 and :459-472 declare every invocation without into and run; a mutant dropping the None guard at pcr.py:163 would raise AttributeError on invocation.into.address. The None value in testimony (pcr.py:172, outside the listed ranges) is not asserted by any test |
| pcr.py:56 | calc returns ResultRef(id) so the return value can be bound by a later invocation | tests/test_semantics.py:377 (`ref == ResultRef('q')`), :452 (`ref == ResultRef('uses-later')`); PCR.calc returns Tick.calc's value unchanged (pcr.py:125-133) |
| pcr.py:86-87 | ticks and the name map start empty per PCR; tick(name) creates on first mention and returns the same Tick afterwards, so later calcs join the existing tick | tests/test_first_class.py:196-202 test_card_testimonies_consume_render_disc_as_fn_ref (two PCR.calc calls naming 'Cards' land in one tick holding both cards; exactly two ticks unpacked at :196); tests/test_semantics.py:459 |
| pcr.py:88 | _writers is per PCR: a second PCR over the same PxC binds a Part written by the first as px:, not fn: | tests/test_semantics.py:538 PCRRunRulesTest.test_cross_pcr_consumer_records_px_not_fn (critic gap 12; killed by the devised globals()-shared writers mutant, mutation-kill.md row 29) |
| pcr.py:91-96 | tick order is first-mention order: a tick named first by a consumer runs before a tick named later by its producer | tests/test_semantics.py:459 PCRRunRulesTest.test_tick_order_is_first_mention_not_producer_declaration (killed by pcr.py:95 insert(0), mutation-kill.md) |
| pcr.py:109-110 | PCR.calc rejects an id already used in any tick of the same PCR | tests/test_semantics.py:309 PCRDeclarationRulesTest.test_pcr_duplicate_id_rejected_across_ticks |
| pcr.py:112-116 | declaration-time rewrite of a Part binding into ResultRef(writer) when the writer was declared earlier in this PCR; no rewrite when the writer is declared later | tests/test_semantics.py:330 test_part_binding_rewritten_to_result_ref_when_writer_declared_first, :346 test_part_binding_not_rewritten_when_writer_declared_after_consumer; tests/test_first_class.py:148, :194 |
| pcr.py:118 | PCR.calc coerces a str into to Part | tests/test_semantics.py:356-363 (into='px.mid' string; the PxC value and testimony are read back), :510-519 (into='px.first' string then pxc.get('px.first')), :529-536 |
| pcr.py:119-123 | a second writer for the same into address raises ValueError; the first writer is recorded in _writers and drives the rewrite | tests/test_semantics.py:320 test_pcr_multiple_writers_rejected; tests/test_first_class.py:166 test_duplicate_writer_rejected; writer registration observed through the rewrite at tests/test_semantics.py:330-344 |
| pcr.py:151-155 | a ResultRef to an id not yet in results raises ValueError at run; declaration accepts it | tests/test_semantics.py:443 (same tick, producer later), :459 (producer in a later tick) |
| pcr.py:156 | an fn: binding passes results[id] itself, not a copy | tests/test_first_class.py:237 SharedResultFanoutTest.test_shared_mutable_result_is_not_copied_between_consumers (dict payload; deepcopy mutant killed, mutation-kill.md row 39) |
| pcr.py:157 | testimony records 'fn:<id>' for a ResultRef binding | tests/test_semantics.py:330-344; tests/test_first_class.py:194-202 |
| pcr.py:159-160 | args silently override same-named bound inputs (call_args.update) | tests/test_semantics.py:426 PCRRunRulesTest.test_args_silently_override_same_named_bound_inputs |
| pcr.py:161 | the value comes from pxc.call over the Calculation registered at pcr.py:142; two Calculation objects sharing an address with different callables make run raise | tests/test_semantics.py:486 PCRRunRulesTest.test_run_registers_calculations_and_rejects_conflicting_address |
| pcr.py:162 | results is a flat dict keyed by invocation id; a later invocation with the same id (via Tick.calc) overwrites | tests/test_semantics.py:521 test_results_keyed_by_id_not_tick_and_rerun_replaces, :393 test_tick_calc_bypasses_pcr_duplicate_id_rule; tests/test_first_class.py:188 test_results_keyed_by_invocation_id |
| pcr.py:163-164 | into publication is immediate and per invocation: a later writer wins, earlier writes survive a mid-run failure (no rollback), and the published object is the results value | tests/test_semantics.py:408 test_tick_calc_bypasses_pcr_multiple_writer_rule, :501 test_failure_mid_run_leaves_prior_writes; tests/test_first_class.py:221 test_published_part_is_the_direct_result_object |
| core.py:18-19 | Part('') raises ValueError; any non-empty prefix is accepted | tests/test_semantics.py:146 ConstructorRulesTest.test_constructor_rules_part_address_non_empty |
| core.py:33-34 | Calculation address must start with 'fn.'; the callable is not inspected | tests/test_semantics.py:156 ConstructorRulesTest.test_constructor_rules_calculation_fn_prefix |
| core.py:58-59 | PxC.get of an unproduced address raises KeyError | tests/test_semantics.py:167 PxCRulesTest.test_pxc_get_missing_raises_keyerror; reached from a PCR run at :474 test_missing_part_fails_only_at_run |
| core.py:60 | PxC.get returns the stored object itself | tests/test_first_class.py:233 (`assertIs(self.pxc.get(part), self.run.results[key])`); tests/test_semantics.py:576 |
| core.py:62-66 | set returns PxWrite kind 'new-address' then 'replacement' and overwrites in place (no versioning) | tests/test_semantics.py:179 PxCRulesTest.test_pxc_set_kinds_new_address_then_replacement_without_versioning |
| core.py:68-71 | register is idempotent for the same callable and raises ValueError for a different callable at the same address, leaving the first in place | tests/test_semantics.py:191 test_pxc_register_same_callable_is_idempotent, :205 test_pxc_register_conflict_on_different_callable |
| pql.py:55 | where() composes the description as '<parent> where …' | tests/test_semantics.py:291 (`refined.description == 'px.* where …'`) |
| pql.py:57-58 | matches() materialises the selection as a tuple: empty for a missing Part, sorted by address for a prefix | tests/test_semantics.py:247 (empty), :288 (sorted), :303 (prefix 'fn.' empty) |
| pql.py:60-61 | values() returns every match's value in match order | tests/test_semantics.py:263 (`values(pxc) == (1, 2)`), :290 |
| pql.py:63-67 | one() raises ValueError unless exactly one match; returns that match's value | tests/test_semantics.py:249-250 (zero -> ValueError), :264-265 (two -> ValueError); tests/test_first_class.py:143 (one match -> value) |
| pql.py:69-72 | optional() raises ValueError for more than one match and returns None for zero | tests/test_semantics.py:248 (zero -> None), :266-267 (two -> ValueError) |

## Notes

- pcr.py:45 and pcr.py:52 are Tick.calc-level rules; the PCR.calc twins (pcr.py:118 coercion, args pass-through at pcr.py:129) are covered. Direct `pcr.tick(name).calc` use is the bypass path the silent-rule tests at tests/test_semantics.py:393 and :408 already exercise, so a one-line addition to either test (`into='px.out'` as a str; `args` mapping mutated after declaration) would close both.
- pcr.py:89 needs a second PCR reusing an id over the same PxC (tests/test_semantics.py:538 already builds two PCRs).
- pql.py:73 needs one `optional()` call with exactly one match (tests/test_semantics.py:238 already has the zero-match case).
- Not counted as missing: pcr.py:172 testimony `into=None` (outside the listed ranges; exercised at tests/test_semantics.py:401 but not asserted).
