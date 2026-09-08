from datetime import date
import unittest

from stats import Description, DiscRecord, MembershipObservation, continuous_membership_runs, description_frequency, distinct_discs_by_mold, later_shot_rate

class StatsTests(unittest.TestCase):
    def test_membership_gap_and_censoring(self):
        rows = [MembershipObservation(date(2026, 1, 1)), MembershipObservation(date(2026, 1, 2)), MembershipObservation(date(2026, 1, 4))]
        self.assertEqual(continuous_membership_runs(rows), (2, 1))
        self.assertEqual(continuous_membership_runs(rows, observation_end=date(2026, 1, 6)), (2, 1))
        self.assertEqual(continuous_membership_runs(rows, observation_end=date(2026, 1, 6), complete_stream=True), (2, 3))
        self.assertEqual(continuous_membership_runs([]), ())

    def test_mold_identity_dedupe_and_conflict(self):
        rows = [DiscRecord("a", "M1", "P1"), DiscRecord("a", "M1", "P1"), DiscRecord("b", "M1", "P1"), DiscRecord("c", "M2", "P2")]
        self.assertEqual(distinct_discs_by_mold(rows), {("M1", "P1"): 2, ("M2", "P2"): 1})
        with self.assertRaises(ValueError):
            distinct_discs_by_mold([DiscRecord("a", "M1", "P1"), DiscRecord("a", "M2", "P1")])

    def test_description_denominators_and_raw_phrases(self):
        result = description_frequency([Description("sam", "a", "stable", "holds its line"), Description("sam", "a", "stable", "very stable"), Description("lee", "b", "glide", "keeps going")])
        self.assertEqual(result["stable"], {"contributor_count": 1, "disc_count": 1, "contributor_denominator": 2, "disc_denominator": 2, "raw_phrases": ("holds its line", "very stable")})

    def test_later_shot_windows_and_empty_denominator(self):
        result = later_shot_rate([False, True], [True, True, False])
        self.assertEqual(result["prior_events"], 1)
        self.assertEqual(result["current_eligible"], 3)
        self.assertAlmostEqual(result["difference_percentage_points"], 16.6666666667)
        self.assertIsNone(later_shot_rate([], [True])["difference_percentage_points"])

if __name__ == "__main__":
    unittest.main()
