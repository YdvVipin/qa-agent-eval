#!/usr/bin/env python3
"""Runs QA Mentor AI's live pipeline against the original 28-question golden
set and the hardened set (28 + 9 adversarial cases), reporting intent
accuracy side by side so a reader can see the harder set is actually harder.

Run with myNanoGpt's venv (needs requests, python-dotenv):
    ../myNanoGpt/.venv/bin/python3 run_hardened_eval.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from adapter import QAMentorAdapter  # noqa: E402


def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def run_set(adapter, items, label):
    rows = []
    for i, item in enumerate(items, 1):
        out = adapter.run(item)
        routed = adapter.intent_of(out)
        ok = routed == item["intent"]
        rows.append({"id": item["id"], "expected": item["intent"], "routed": routed,
                      "intent_ok": ok, "error": out["error"]})
        print(f"  [{label}][{i:>2}/{len(items)}] {item['id']:<10} "
              f"expected={item['intent']:<9} routed={str(routed):<9} {'OK' if ok else 'MISS'}")
    scored = [r for r in rows if not r["error"]]
    accuracy = sum(r["intent_ok"] for r in scored) / len(scored) if scored else 0.0
    return {"label": label, "n": len(scored), "intent_accuracy": round(accuracy, 3), "rows": rows}


def main():
    adapter = QAMentorAdapter()
    original = load_jsonl(HERE / "goldens" / "original_28.jsonl")
    hard = load_jsonl(HERE / "goldens" / "hard_cases.jsonl")

    print("Running original 28-question set...")
    original_report = run_set(adapter, original, "original-28")

    print("\nRunning hardened set (28 + 9 adversarial cases)...")
    hardened_report = run_set(adapter, original + hard, "hardened-37")

    print("\n" + "=" * 60)
    print(f"  Original 28:  intent accuracy = {original_report['intent_accuracy']:.0%}")
    print(f"  Hardened 37:  intent accuracy = {hardened_report['intent_accuracy']:.0%}")
    print("=" * 60)

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"hardened_eval_{stamp}.json"
    out_path.write_text(json.dumps({"original": original_report, "hardened": hardened_report}, indent=2))
    print(f"\nSaved -> {out_path}")


if __name__ == "__main__":
    main()
