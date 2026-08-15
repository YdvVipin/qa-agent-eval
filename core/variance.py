"""N-inputs x K-runs variance harness — tells real regressions from
run-to-run noise. The regression band is mean +/- 2 sigma from a baseline's
own K runs."""
import statistics
from typing import Callable


def run_k_times(adapter, input: dict, k: int, score_fn: Callable[[dict], float]) -> list[float]:
    """Run one input K times through the adapter, return the K scores."""
    return [score_fn(adapter.run(input)) for _ in range(k)]


def variance_report(scores: list[float]) -> dict:
    """Mean, stdev, and the 2-sigma regression band for one input's K scores."""
    if len(scores) < 2:
        raise ValueError("need at least 2 runs to compute variance")
    mean = statistics.mean(scores)
    sigma = statistics.stdev(scores)
    return {
        "mean": mean,
        "stdev": sigma,
        "n": len(scores),
        "regression_floor": mean - 2 * sigma,
        "regression_ceiling": mean + 2 * sigma,
    }


def is_regression(new_score: float, baseline: dict) -> bool:
    """True if new_score falls BELOW the baseline's 2-sigma floor (a regression,
    not an improvement — those aren't flagged by this check)."""
    return new_score < baseline["regression_floor"]


def run_variance_suite(adapter, inputs: list[dict], k: int, score_fn: Callable[[dict], float]) -> dict:
    """Run N inputs x K runs each, return a per-input and overall variance report."""
    per_input = {}
    all_scores = []
    for i, item in enumerate(inputs):
        item_id = item.get("id", str(i))
        scores = run_k_times(adapter, item, k, score_fn)
        per_input[item_id] = variance_report(scores)
        all_scores.extend(scores)
    return {"per_input": per_input, "overall": variance_report(all_scores)}


def demo():
    class FakeAdapter:
        def __init__(self, scores):
            self._scores = iter(scores)

        def run(self, input):
            return {"score": next(self._scores)}

    adapter = FakeAdapter([1.0, 1.0, 1.0, 1.0, 1.0])
    scores = run_k_times(adapter, {"id": "x"}, 5, lambda o: o["score"])
    report = variance_report(scores)
    assert report["mean"] == 1.0
    assert report["stdev"] == 0.0
    assert not is_regression(1.0, report)
    assert is_regression(0.0, report)  # below the floor: flagged
    assert not is_regression(5.0, report)  # above the ceiling (an improvement): not flagged

    try:
        variance_report([0.3])
        assert False, "should have raised on n<2"
    except ValueError:
        pass

    print("variance.py self-check OK")


if __name__ == "__main__":
    demo()
