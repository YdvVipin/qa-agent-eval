#!/usr/bin/env python3
"""K=3 variance check on a subset of the goldens, using core/variance.py's
run_k_times + variance_report unchanged — the same artefact CS01 produces for
QA Mentor AI's routing. qa-spine's server never calls a model, so the expected
result is zero variance; this run measures that rather than assuming it.

Run: python3 run_variance_check.py   (stdlib only; needs the sibling qa-spine checkout)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from adapter import QASpineAdapter  # noqa: E402
from run_eval import load_goldens, score  # noqa: E402
from core.variance import run_k_times, variance_report  # noqa: E402

# One per path: clean audit, quote check, all-or-nothing batch, gate block,
# gate pass after an answer, fixture rejection.
SUBSET_IDS = {"cs02-01", "cs02-05", "cs02-11", "cs02-14", "cs02-15", "cs02-23"}
K = 3


def main():
    adapter = QASpineAdapter()
    items = [it for it in load_goldens() if it["id"] in SUBSET_IDS]
    assert len(items) == len(SUBSET_IDS), f"expected {len(SUBSET_IDS)} items, found {len(items)}"

    # Each item has its own expected outcome, so score_fn is built per item (as in CS01).
    per_input, all_scores = {}, []
    for item in items:
        scores = run_k_times(adapter, item, K, lambda o, it=item: score(it, o))
        per_input[item["id"]] = variance_report(scores)
        all_scores.extend(scores)
        print(f"{item['id']}  scores={scores}  {item['rule']}")

    overall = variance_report(all_scores)
    out = HERE / "results" / "cs02_variance_check.json"
    out.write_text(json.dumps({"per_input": per_input, "overall": overall, "k": K,
                               "subset": sorted(SUBSET_IDS)}, indent=2))
    print(f"\nOverall: mean={overall['mean']:.1%} stdev={overall['stdev']:.3f}")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
