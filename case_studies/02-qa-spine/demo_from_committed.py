#!/usr/bin/env python3
"""Prints this case study's headline numbers from the committed results/ files.
No qa-spine checkout or Node needed. Exits non-zero if a results file is
missing or lacks an expected key.

Run: python3 demo_from_committed.py
"""
import json
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"


def main():
    try:
        evals = sorted(RESULTS.glob("cs02_eval_*.json"))
        if not evals:
            sys.exit(f"ERROR: no cs02_eval_*.json in {RESULTS}")
        e = json.loads(evals[-1].read_text())
        passed = sum(r["pass"] for r in e["rows"])
        print(f"Tier 1 — golden accept/reject/exit-code accuracy: {e['tier1_accuracy']:.0%} ({passed}/{e['n']})"
              f"  [{evals[-1].name}]")

        v = json.loads((RESULTS / "cs02_variance_check.json").read_text())
        o = v["overall"]
        print(f"Variance (K={v['k']}, {len(v['subset'])} inputs): mean={o['mean']:.2f} stdev={o['stdev']:.2f} n={o['n']}")
    except (OSError, json.JSONDecodeError) as err:
        sys.exit(f"ERROR: cannot read results: {err}")
    except KeyError as err:
        sys.exit(f"ERROR: expected key {err} missing from a results file")


if __name__ == "__main__":
    main()
