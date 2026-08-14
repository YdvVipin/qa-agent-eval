"""Tier classification for scores: tier-1 (deterministic), tier-2
(reference-based), tier-3 (judge-based). core/ never computes system-specific
scores itself — each case study's adapter produces raw scores; this module
aggregates and labels them so variance.py and judge_agreement.py can consume
any system's results the same way."""

TIER_1 = "deterministic"
TIER_2 = "reference_based"
TIER_3 = "judge_based"


def aggregate(rows: list[dict], score_key: str) -> dict:
    """Mean/min/max of one score field across a list of result rows, skipping
    rows where the field is missing or None."""
    values = [r[score_key] for r in rows if r.get(score_key) is not None]
    if not values:
        raise ValueError(f"no non-null values for {score_key!r}")
    return {"mean": sum(values) / len(values), "min": min(values), "max": max(values), "n": len(values)}


def classify_tier(metric_name: str, tier_map: dict) -> str:
    """Look up which tier a named metric belongs to, given a case study's own
    map, e.g. {"intent_accuracy": TIER_1, "keyword_coverage": TIER_2,
    "judge_score": TIER_3}."""
    if metric_name not in tier_map:
        raise KeyError(f"metric {metric_name!r} not registered in tier_map")
    return tier_map[metric_name]


def demo():
    rows = [{"keyword_coverage": 1.0}, {"keyword_coverage": 0.5}, {"keyword_coverage": None}]
    agg = aggregate(rows, "keyword_coverage")
    assert agg["n"] == 2
    assert agg["mean"] == 0.75
    assert agg["min"] == 0.5 and agg["max"] == 1.0

    tier_map = {"intent_accuracy": TIER_1, "keyword_coverage": TIER_2, "judge_score": TIER_3}
    assert classify_tier("intent_accuracy", tier_map) == TIER_1
    try:
        classify_tier("unknown_metric", tier_map)
        assert False, "should have raised"
    except KeyError:
        pass

    print("metrics.py self-check OK")


if __name__ == "__main__":
    demo()
