#!/usr/bin/env python3
"""Scores the Tier 1 out_of_scope_refused metric (metrics_oos.py) on the
off-topic goldens against QA Mentor AI's live pipeline. The hardened-eval
results don't store answers, so this runs live and saves each full answer into
the results JSON, so the score can be re-checked offline. K runs per item,
because the first single run showed hard-06's redirect isn't stable.

Live, with myNanoGpt's venv, from this directory (case_studies/01-qa-mentor-ai/):
    ../../../myNanoGpt/.venv/bin/python3 run_oos_eval.py
Re-score a saved run's stored answers in place (stdlib only, no server), e.g.
after changing metrics_oos.py or the goldens' off_topic_markers:
    python3 run_oos_eval.py --rescore results/oos_eval_<timestamp>.json
"""
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from metrics_oos import is_graceful_redirect  # noqa: E402
from core.variance import variance_report  # noqa: E402

K = 3


def run_live(items):
    from adapter import QAMentorAdapter  # needs myNanoGpt's venv; not needed for --rescore
    adapter = QAMentorAdapter()
    rows = []
    for item in items:
        for run in range(1, K + 1):
            out = adapter.run(item)
            rows.append({"id": item["id"], "run": run, "question": item["question"],
                         "expected_intent": item["intent"], "routed_intent": adapter.intent_of(out),
                         "error": out["error"], "answer": out["answer"]})
    return rows


def main():
    items = [json.loads(line) for line in open(HERE / "goldens" / "oos_cases.jsonl") if line.strip()]
    markers = {it["id"]: it["off_topic_markers"] for it in items}

    if sys.argv[1:2] == ["--rescore"]:
        out = Path(sys.argv[2])
        rows = json.loads(out.read_text())["rows"]
    else:
        out = HERE / "results" / f"oos_eval_{datetime.now():%Y%m%d-%H%M%S}.json"
        rows = run_live(items)

    for r in rows:
        r["out_of_scope_refused"] = None if r["error"] else is_graceful_redirect(r["answer"], markers[r["id"]])
        print(f"{r['id']:<8} run={r['run']} routed={str(r['routed_intent']):<9} "
              f"{'ERROR ' + r['error'] if r['error'] else 'PASS' if r['out_of_scope_refused'] else 'FAIL'}")

    scored = [r for r in rows if r["out_of_scope_refused"] is not None]
    passed = sum(r["out_of_scope_refused"] for r in scored)
    rate = passed / len(scored) if scored else 0.0
    per_input = {}
    for item in items:
        scores = [float(r["out_of_scope_refused"]) for r in scored if r["id"] == item["id"]]
        if len(scores) >= 2:  # variance_report needs 2+; errored runs are dropped
            per_input[item["id"]] = variance_report(scores)
    result = {"metric": "out_of_scope_refused", "tier": "deterministic", "k": K, "n": len(scored),
              "out_of_scope_refused_rate": rate, "per_input": per_input, "rows": rows}

    out.write_text(json.dumps(result, indent=2))
    print(f"\nout_of_scope_refused: {rate:.0%} ({passed}/{len(scored)})")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
