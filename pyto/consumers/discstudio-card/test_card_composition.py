import copy
import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, "/mnt/d/pyto-worktrees/core/src")
sys.path.insert(0, os.path.dirname(__file__))

from card_composition import compose, execute_card, normalize_recipe


def recipe():
    active = {
        "presentationId": "active", "physicalDiscId": "disc-1", "name": "Warm Mako",
        "note": "first run", "color": "#4c9bc6", "flightValues": {"flight1": 5, "flight2": 4, "flight3": -1, "flight4": 1},
        "positions": {"disc": {"x": 50, "y": 43}},
    }
    rival = {**active, "presentationId": "rival", "physicalDiscId": "disc-2", "name": "Rival"}
    return {"schemaVersion": 3, "presentationId": "active", "physicalDiscId": "disc-1",
            "cards": {"single": {"type": "single", "layout": "standard", "details": True, "discRecipeIds": ["active"]},
                      "battle": {"type": "battle", "layout": "standard", "details": True, "discRecipeIds": ["active", "rival"]}},
            "presentations": {"active": active, "rival": rival}}


class CardCompositionTest(unittest.TestCase):
    def test_shared_active_disc_and_independent_snapshot(self):
        value = recipe()
        output, evidence = execute_card(value)
        self.assertEqual(output["cards"]["single"]["participants"][0]["presentationId"], "active")
        self.assertEqual(output["cards"]["battle"]["participants"][0]["name"], "Warm Mako")
        value["presentations"]["active"]["name"] = "changed after run"
        self.assertEqual(output["cards"]["battle"]["participants"][0]["name"], "Warm Mako")
        self.assertEqual(evidence["composition"]["pcr"], "card-composition")
        self.assertEqual(evidence["composition"]["ticks"][0]["calculations"][0]["calculation"], "fn.card.compose")

    def test_layout_does_not_mutate_disc_input(self):
        value = recipe(); before = copy.deepcopy(value["presentations"])
        value["cards"]["single"]["layout"] = "gallery"
        compose(value)
        self.assertEqual(value["presentations"], before)

    def test_legacy_adapter_has_no_physical_identity(self):
        legacy = {"discId": "old-presentation", "name": "Legacy", "cards": {}}
        normalized = normalize_recipe(legacy)
        self.assertNotIn("physicalDiscId", normalized)
        self.assertEqual(normalized["presentationId"], "old-presentation")

    def test_malformed_reference_rejected(self):
        value = recipe(); value["cards"]["battle"]["discRecipeIds"] = ["active", "missing"]
        with self.assertRaisesRegex(ValueError, "missing"):
            normalize_recipe(value)

    def test_result_hash_is_stable(self):
        first, _ = execute_card(recipe()); second, _ = execute_card(recipe())
        self.assertEqual(hashlib.sha256(json.dumps(first, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(),
                         hashlib.sha256(json.dumps(second, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest())

    def test_card_owns_layout_and_manual_display_fields(self):
        value = recipe()
        value["positions"] = {"disc": {"x": 8, "y": 9}}
        value["group"] = True
        value["cards"]["single"].update({"positions": {"disc": {"x": 20, "y": 30}}, "group": True,
                                           "appearance": "showcase", "hierarchy": "identity-first",
                                           "framing": "border", "title": "Warm paper", "selected": "disc"})
        output, evidence = execute_card(value)
        single = output["cards"]["single"]
        self.assertEqual(single["appearance"], "showcase")
        self.assertEqual(single["positions"]["disc"]["x"], 20)
        self.assertNotIn("positions", single["participants"][0])
        testimony = evidence["composition"]["ticks"][0]["calculations"][0]
        self.assertIn("p0", testimony["inputs"])

    def test_non_string_reference_rejected_without_type_error(self):
        value = recipe(); value["cards"]["battle"]["discRecipeIds"] = ["active", {"bad": True}]
        with self.assertRaises(ValueError):
            normalize_recipe(value)


if __name__ == "__main__":
    unittest.main()
