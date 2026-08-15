#!/usr/bin/env python3
"""Small K=3 variance check of QA Mentor AI's own intent routing, using
core/variance.py's run_variance_suite against the real live pipeline — closes
the gap where the variance harness was only ever exercised against the
separate fine-tune codegen model, never against this case study's own system.

Run with myNanoGpt's venv:
    ../myNanoGpt/.venv/bin/python3 run_variance_check.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from adapter import QAMentorAdapter  # noqa: E402
from core.variance import run_variance_suite  # noqa: E402

# A small, deliberately mixed subset spanning intents and two boundary cases —
# kept small (K=3 x 6 items = 18 live calls) to stay fast, not exhaustive.
SUBSET_IDS = {"mentor-01", "strategy-01", "testgen-01", "reviewer-01", "hard-04", "hard-09"}
K = 3


def load_items():
    items = []
    for fname in ["goldens/original_28.jsonl", "goldens/hard_cases.jsonl"]:
        with open(HERE / fname) as f:
            items += [json.loads(line) for line in f if line.strip()]
    return [it for it in items if it["id"] in SUBSET_IDS]


def main():
    adapter = QAMentorAdapter()
    items = load_items()
    assert len(items) == len(SUBSET_IDS), f"expected {len(SUBSET_IDS)} items, found {len(items)}"

    def score_fn(output):
        return 1.0  # placeholder, replaced per-item below since expected intent varies

    # run_variance_suite's score_fn doesn't know the expected intent per item, so build
    # one closure per item instead of using a single shared score_fn.
    from core.variance import run_k_times, variance_report

    per_input = {}
    all_scores = []
    for item in items:
        expected = item["intent"]
        scores = run_k_times(adapter, item, K, lambda o, exp=expected: 1.0 if adapter.intent_of(o) == exp else 0.0)
        per_input[item["id"]] = variance_report(scores)
        all_scores.extend(scores)
        print(f"{item['id']:<12} expected={expected:<9} scores={scores}")

    overall = variance_report(all_scores)
    result = {"per_input": per_input, "overall": overall, "k": K, "subset": sorted(SUBSET_IDS)}

    out = HERE / "results" / "qa_mentor_variance_check.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nOverall: mean={overall['mean']:.1%} stdev={overall['stdev']:.3f}")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
