#!/usr/bin/env python3
"""Prints this case study's headline numbers from the committed results/ files.

No live server, no OPENAI_API_KEY, no myNanoGpt checkout needed — a clean clone is
enough. Exits non-zero if a results file is missing or lacks an expected key.

Run: python3 demo_from_committed.py
"""
import json
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"


def load(name):
    path = RESULTS / name
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"ERROR: cannot read {path}: {e}")


def main():
    try:
        h = load("hardened_eval_20260814-043058.json")
        print("Tier 1 — intent routing accuracy")
        for s in ("original", "hardened"):
            print(f"  {h[s]['label']:<12} n={h[s]['n']:<3} {h[s]['intent_accuracy']:.0%}")

        runs = [load(p.name) for p in sorted(RESULTS.glob("oos_eval_*.json"))]
        if not runs:
            sys.exit(f"ERROR: no oos_eval_*.json in {RESULTS}")
        passed = sum(r["out_of_scope_refused_rate"] * r["n"] for r in runs)
        total = sum(r["n"] for r in runs)
        print(f"\nTier 1 — out_of_scope_refused ({len(runs)} runs of K={runs[0]['k']}): "
              f"{passed / total:.0%} ({round(passed)}/{total})")

        v = load("qa_mentor_variance_check.json")["overall"]
        print(f"\nRouting variance (K=3): mean={v['mean']:.2f} stdev={v['stdev']:.2f} n={v['n']}")

        k = load("keyword_coverage_headline.json")
        print(f"\nTier 2 — keyword coverage (n={k['n']}): {k['keyword_coverage']:.1%}  [source: {k['source']}]")

        j = load("judge_agreement_report.json")
        rater = j.get("reference_rater", "controller")
        n = j["n_human"] if rater == "human" else j["n"]
        print(f"\nTier 3 — judge agreement vs {rater} labels (n={n})")
        print(f"  raw agreement {j['raw_agreement']:.0%}, Cohen's kappa {j['cohens_kappa']:.2f}")
        print(f"  {j['verdict']}")

        f = load("finetune_variance_report.json")
        print(f"\nThe correction — fine-tune codegen compile rate (K={f['k']})")
        for model, s in f["per_model"].items():
            print(f"  {model:<18} mean={s['mean']:.3f} stdev={s['stdev']:.3f}")
        print(f"  regressed (2-sigma band): {f['regressed']}; base won {f['base_wins']}/{f['k']} paired runs")
    except KeyError as e:
        sys.exit(f"ERROR: expected key {e} missing from a results file")


if __name__ == "__main__":
    main()
