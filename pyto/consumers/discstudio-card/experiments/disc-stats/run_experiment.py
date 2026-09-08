from datetime import date

from pyto import Calculation, PCR, Part, PxC
from stats import Description, DiscRecord, MembershipObservation, continuous_membership_runs, description_frequency, distinct_discs_by_mold, later_shot_rate

fixture = {
    "membership": [MembershipObservation(date(2026, 1, 1)), MembershipObservation(date(2026, 1, 2)), MembershipObservation(date(2026, 1, 4))],
    "discs": [DiscRecord("a", "M1", "P1"), DiscRecord("a", "M1", "P1"), DiscRecord("b", "M1", "P1"), DiscRecord("c", "M2", "P2")],
    "descriptions": [Description("sam", "a", "stable", "holds its line"), Description("sam", "a", "stable", "very stable"), Description("lee", "b", "glide", "keeps going")],
    "prior_shots": [False, True], "current_shots": [True, True, False],
}

def annotate(args):
    fixture = args["value"]
    return {"membership_runs": continuous_membership_runs(fixture["membership"]), "mold_counts": distinct_discs_by_mold(fixture["discs"]), "description_frequency": description_frequency(fixture["descriptions"]), "later_shot_rate": later_shot_rate(fixture["prior_shots"], fixture["current_shots"])}

pxc = PxC()
source, output = Part("px.synthetic.disc_history"), Part("px.synthetic.disc_stats")
pxc.set(source, fixture)
pcr = PCR("synthetic-disc-statistics")
pcr.calc("stats", Calculation("fn.discStats", annotate), id="annotate", value=source, into=output)
run = pcr.run(pxc)
print(run)
print(pxc.get(output))
