#!/usr/bin/env python3
"""Reads the filled-in labeling sheet + the judge's scores, computes raw
agreement and Cohen's kappa via core/judge_agreement.py.

Run: python3 compute_judge_agreement.py   (stdlib only, no myNanoGpt venv needed)
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # agent-evals root, for `core`
from core.judge_agreement import raw_agreement, cohens_kappa  # noqa: E402


def main():
    sample_path = HERE / "results" / "judge_sample.json"
    sheet_path = HERE / "results" / "judge_labeling_sheet.csv"

    judged = {r["id"]: r["judge_score"] for r in json.loads(sample_path.read_text())}

    human = {}
    with open(sheet_path) as f:
        for row in csv.DictReader(f):
            val = row["human_score_1_to_5"].strip()
            if not val:
                sys.exit(f"ERROR: {row['id']} has no human score — fill in {sheet_path} first")
            human[row["id"]] = int(val)

    ids = sorted(judged)
    judge_labels = [judged[i] for i in ids]
    human_labels = [human[i] for i in ids]

    agreement = raw_agreement(judge_labels, human_labels)
    kappa = cohens_kappa(judge_labels, human_labels)

    print(f"n = {len(ids)}")
    print(f"Raw agreement:  {agreement:.0%}")
    print(f"Cohen's kappa:  {kappa:.2f}")
    if kappa < 0.4:
        verdict = "WEAK: judge scores should not be trusted as a standalone quality signal."
    elif kappa < 0.6:
        verdict = "MODERATE: judge is directionally useful but noisy at the item level."
    else:
        verdict = "STRONG: judge agrees with the reference labels well enough to trust for this rubric."
    print(f"-> {verdict}")

    out = HERE / "results" / "judge_agreement_report.json"
    out.write_text(json.dumps({"n": len(ids), "raw_agreement": agreement, "cohens_kappa": kappa,
                                "verdict": verdict}, indent=2))
    print(f"\nSaved -> {out}")


if __name__ == "__main__":
    main()
