#!/usr/bin/env python3
"""Generates the 30-item judge-reliability sample: runs the live pipeline,
scores each answer with the gpt-4o-mini judge (reused from myNanoGpt's
run_evals.py — same rubric: correctness + completeness, 1-5), and writes a
labeling sheet for independent scoring (see the case study README for how
this specific run's labels were produced). The judge score is recorded but
NOT shown alongside the blank column, so the independent label isn't
anchored by the judge's answer.

Run with myNanoGpt's venv (needs requests, python-dotenv, openai):
    ../myNanoGpt/.venv/bin/python3 generate_judge_sample.py
"""
import csv
import json
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MYNANOGPT_ROOT = Path(os.environ.get("MYNANOGPT_ROOT", HERE.parents[2] / "myNanoGpt"))
sys.path.insert(0, str(MYNANOGPT_ROOT))

from evals.run_evals import ask_agent, llm_judge  # noqa: E402

BASE_URL = os.environ.get("QA_MENTOR_BASE_URL", "http://localhost:8004")
SAMPLE_SIZE = 30
SEED = 20260814  # fixed: reproducible sample


def load_all_cases():
    cases = []
    with open(HERE / "goldens" / "original_28.jsonl") as f:
        cases += [json.loads(line) for line in f if line.strip()]
    with open(HERE / "goldens" / "hard_cases.jsonl") as f:
        cases += [json.loads(line) for line in f if line.strip()]
    return cases


def main():
    cases = load_all_cases()
    random.Random(SEED).shuffle(cases)
    sample = cases[:SAMPLE_SIZE]

    rows = []
    for i, item in enumerate(sample, 1):
        print(f"[{i}/{len(sample)}] {item['id']}", flush=True)
        agent, answer, sources, error = ask_agent(BASE_URL, item["question"])
        if error or not answer:
            print(f"  SKIP (error: {error})")
            continue
        judge_score, judge_reason = llm_judge(item["question"], answer, item.get("keywords", []))
        rows.append({"id": item["id"], "question": item["question"], "answer": answer,
                      "judge_score": judge_score, "judge_reason": judge_reason})

    results_dir = HERE / "results"
    results_dir.mkdir(exist_ok=True)

    out_json = results_dir / "judge_sample.json"
    out_json.write_text(json.dumps(rows, indent=2))

    out_csv = results_dir / "judge_labeling_sheet.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "question", "answer", "human_score_1_to_5"])
        for r in rows:
            w.writerow([r["id"], r["question"], r["answer"], ""])

    print(f"\nWrote {len(rows)} judged answers -> {out_json}")
    print(f"Wrote labeling sheet -> {out_csv}")
    print("Fill in the human_score_1_to_5 column (1-5, correctness+completeness), "
          "then run compute_judge_agreement.py")


if __name__ == "__main__":
    main()
