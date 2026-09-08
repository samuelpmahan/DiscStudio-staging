"""Small, explicit statistics for synthetic disc-history annotations."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Sequence

@dataclass(frozen=True)
class MembershipObservation:
    day: date
    member: bool = True

def continuous_membership_runs(observations: Sequence[MembershipObservation], *, observation_end: date | None = None, complete_stream: bool = False) -> tuple[int, ...]:
    """Return observed daily runs; gaps end runs and incomplete streams stay censored."""
    active_days = sorted({item.day for item in observations if item.member})
    if not active_days:
        return ()
    runs: list[int] = []
    start = previous = active_days[0]
    for current in active_days[1:]:
        if current != previous + timedelta(days=1):
            runs.append((previous - start).days + 1)
            start = current
        previous = current
    end = observation_end if complete_stream and observation_end is not None and observation_end >= previous else previous
    runs.append((end - start).days + 1)
    return tuple(runs)

@dataclass(frozen=True)
class DiscRecord:
    disc_id: str
    mold: str
    plastic: str

def distinct_discs_by_mold(records: Iterable[DiscRecord]) -> dict[tuple[str, str], int]:
    seen: dict[str, tuple[str, str]] = {}
    for record in records:
        label = (record.mold, record.plastic)
        if record.disc_id in seen and seen[record.disc_id] != label:
            raise ValueError(f"disc {record.disc_id!r} has conflicting mold/plastic labels")
        seen[record.disc_id] = label
    counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    for label in seen.values():
        counts[label] += 1
    return dict(sorted(counts.items()))

@dataclass(frozen=True)
class Description:
    contributor: str
    disc_id: str
    term: str
    raw_phrase: str

def description_frequency(rows: Iterable[Description]) -> dict[str, dict[str, object]]:
    grouped: defaultdict[str, list[Description]] = defaultdict(list)
    for row in rows:
        grouped[row.term].append(row)
    all_contributors = {row.contributor for rows in grouped.values() for row in rows}
    all_discs = {row.disc_id for rows in grouped.values() for row in rows}
    return {term: {
        "contributor_count": len({row.contributor for row in term_rows}),
        "disc_count": len({row.disc_id for row in term_rows}),
        "contributor_denominator": len(all_contributors),
        "disc_denominator": len(all_discs),
        "raw_phrases": tuple(row.raw_phrase for row in term_rows),
    } for term, term_rows in sorted(grouped.items())}

def later_shot_rate(prior: Sequence[bool], current: Sequence[bool]) -> dict[str, object]:
    def rate(events: Sequence[bool]) -> float | None:
        return sum(events) / len(events) if events else None
    prior_rate, current_rate = rate(prior), rate(current)
    return {
        "prior_events": sum(prior), "prior_eligible": len(prior), "prior_rate": prior_rate,
        "current_events": sum(current), "current_eligible": len(current), "current_rate": current_rate,
        "difference_percentage_points": None if prior_rate is None or current_rate is None else (current_rate - prior_rate) * 100,
    }
