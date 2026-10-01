#!/usr/bin/env python3
"""Runs every golden in goldens/smoke.jsonl once through QASpineAdapter and
reports Tier 1 (deterministic) accuracy: the final step's exit code matches the
golden, and when the golden names an error, the error message contains it.

Run: python3 run_eval.py   (stdlib only; needs the sibling qa-spine checkout)
"""
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from adapter import QASpineAdapter  # noqa: E402


def load_goldens():
    return [json.loads(line) for line in open(HERE / "goldens" / "smoke.jsonl") if line.strip()]


def score(item, output) -> float:
    exp = item["expected"]
    ok = output["exit_code"] == exp["exit_code"]
    if ok and "error_contains" in exp:
        ok = exp["error_contains"] in (output["error"] or "")
    return 1.0 if ok else 0.0


def main():
    adapter = QASpineAdapter()
    rows = []
    for item in load_goldens():
        out = adapter.run(item)
        s = score(item, out)
        rows.append({"id": item["id"], "rule": item["rule"], "expected": item["expected"],
                     "exit_code": out["exit_code"], "outcome": adapter.intent_of(out),
                     "error": out["error"], "pass": s == 1.0})
        print(f"{item['id']}  {'PASS' if s else 'FAIL'}  exit={out['exit_code']}  {item['rule']}")
        if not s:
            print(f"         got error: {out['error']}")

    accuracy = sum(r["pass"] for r in rows) / len(rows)
    out_path = HERE / "results" / f"cs02_eval_{datetime.now():%Y%m%d-%H%M%S}.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps({"n": len(rows), "tier1_accuracy": accuracy, "rows": rows}, indent=2))
    print(f"\nTier 1 accuracy: {accuracy:.0%} ({sum(r['pass'] for r in rows)}/{len(rows)})")
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()
