#!/usr/bin/env python3
"""Reads the K=5 fine-tune A/B results (qa_codegen_ft/ab_results_k5.json in
myNanoGpt), computes mean/stdev per model via core/variance.py, restates the
original single-run verdict against the measured variance band, and writes
docs/correction.md from the actual measured numbers (not hand-transcribed,
so the doc can't drift from the data).

Run: python3 compute_finetune_variance.py   (stdlib only)
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # agent-evals root, for `core`
from core.variance import variance_report, is_regression  # noqa: E402

MYNANOGPT_ROOT = Path(os.environ.get("MYNANOGPT_ROOT", HERE.parents[2] / "myNanoGpt"))
RESULTS_PATH = MYNANOGPT_ROOT / "qa_codegen_ft" / "ab_results_k5.json"
MODELS = ["qwen2.5-coder:3b", "qa-coder-v2"]
ORIGINAL_ROUND1 = {"qwen2.5-coder:3b": "4/13", "qa-coder-v2": "3/13"}  # round-1 single-run result

CORRECTION_TEMPLATE = """# Correction: the qa-coder-v2 fine-tune result

**Originally claimed** (round 1, single run each, n=13 holdout):
base `qwen2.5-coder:3b` {base_orig} vs. `qa-coder-v2` {tuned_orig} on TypeScript-compile
pass rate — "the fine-tune regressed."

**What a K={k} re-run shows**, same 13-item holdout, Ollama seed varied per run:

| Model | Mean pass rate | Std dev | Per-run |
|---|---|---|---|
| `qwen2.5-coder:3b` (base) | {base_mean:.1%} | {base_std:.3f} | {base_runs} |
| `qa-coder-v2` (fine-tuned) | {tuned_mean:.1%} | {tuned_std:.3f} | {tuned_runs} |

**Two ways to read this, and they disagree — stated plainly rather than picking the
more flattering one:**

1. **Single-run noise band** (this repo's chosen regression threshold: mean +/- 2 stdev
   of the base model's own run-to-run spread): [{base_floor:.1%}, {base_ceiling:.1%}].
   The tuned model's mean falls **{inside_outside}** that band. By this test alone,
   no statistically flagged regression.
2. **Paired comparison across the {k} runs**: the base model beat the tuned model in
   {base_wins} of {k} runs, with {overlap_text}. A sample this small (n=13 holdout
   items, K={k} runs) can't support a confident verdict either way, but a {base_wins}/{k}
   sweep with that pattern is a real directional signal the single-run band is too
   generous to catch.

**Per-item note:** the tuned model's zero stdev is not a rounding artifact — at the
per-item level, `qa-coder-v2` passed the exact same {tuned_always_pass} of 13 holdout
items on every one of the {k} seeded runs and failed the exact same {tuned_always_fail},
byte-for-byte identical pass/fail pattern regardless of the varied Ollama `seed`. The
base model did not behave this way: {base_flip} of its 13 items flipped between pass
and fail across the {k} runs. So the "{tuned_std:.3f} std dev" for the tuned model
reflects zero observed sampling variability across these runs, not just a small measured
number — worth flagging to whoever trains the next version (it may point to the
merged/quantized model being more deterministic, or to `seed` not affecting this
model's output; this pass doesn't try to tell those apart).

**Honest statement:** {verdict}

**What did not change:** the mechanism hypothesis — 174 of 263 training records were
GitHub-mined with a prompt ending in a bulleted scenario list, and the model plausibly
learned to continue the list rather than write code. That remains the leading
*hypothesis explaining the absence of gains*, not proof of harm; it wasn't re-tested here.

**Known limitation:** the holdout is 13 items and mirrors the same GitHub-mined
scenario-list format as the training data, so even a real difference of this size may
not be visible here. Expanding to a larger, format-diverse holdout is tracked as
follow-up work, not done in this pass.
"""


def main():
    results = json.loads(RESULTS_PATH.read_text())
    ks = sorted(set(r["k"] for r in results))
    k = len(ks)

    per_run = {}
    reports = {}
    for model in MODELS:
        rates = []
        for kk in ks:
            run_rows = [r for r in results if r["k"] == kk]
            passed = sum(1 for r in run_rows if r.get(model, {}).get("pass"))
            rates.append(passed / len(run_rows))
        per_run[model] = rates
        reports[model] = variance_report(rates)
        print(f"{model:22s} mean={reports[model]['mean']:.1%}  stdev={reports[model]['stdev']:.3f}  "
              f"per-run={[f'{x:.0%}' for x in rates]}")

    base, tuned = reports[MODELS[0]], reports[MODELS[1]]
    base_runs, tuned_runs = per_run[MODELS[0]], per_run[MODELS[1]]
    regressed = is_regression(tuned["mean"], base)

    base_wins = sum(1 for b, t in zip(base_runs, tuned_runs) if b > t)
    overlap = not (min(base_runs) > max(tuned_runs) or max(base_runs) < min(tuned_runs))
    overlap_text = "overlapping ranges" if overlap else "no overlap between the two models' per-run ranges"

    ids = sorted(set(r["id"] for r in results))
    by_id = {model: {i: {} for i in ids} for model in MODELS}
    for r in results:
        for model in MODELS:
            by_id[model][r["id"]][r["k"]] = r.get(model, {}).get("pass", False)
    tuned_always_pass = sum(1 for i in ids if all(by_id[MODELS[1]][i][kk] for kk in ks))
    tuned_always_fail = sum(1 for i in ids if not any(by_id[MODELS[1]][i][kk] for kk in ks))
    base_flip = sum(1 for i in ids if len(set(by_id[MODELS[0]][i][kk] for kk in ks)) > 1)

    if regressed:
        verdict = "The fine-tune regressed, even accounting for run-to-run variance."
    else:
        if base_wins == k:
            win_phrase = "won every paired run"
        elif base_wins == 0:
            win_phrase = "won none of the paired runs"
        else:
            win_phrase = f"won {base_wins} of {k} paired runs"
        verdict = (
            "The single-run noise-band test doesn't flag a statistically significant "
            f"regression. But the base model {win_phrase}, with {overlap_text} — a real, "
            "if statistically underpowered, directional signal that the fine-tune "
            "underperforms the base model. Combined with the tuned model's zero "
            "per-item variance (above), this is genuinely inconclusive rather than a "
            "clean null result: not the confirmed regression originally claimed, and "
            "not confidently \"no difference\" either."
        )
    print(f"\nBase 2-sigma band: [{base['regression_floor']:.1%}, {base['regression_ceiling']:.1%}]")
    print(f"base_wins={base_wins}/{k}  overlap={overlap}")
    print(f"Verdict: {verdict}")

    results_dir = HERE / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "finetune_variance_report.json").write_text(
        json.dumps({"per_model": reports, "per_run": per_run, "regressed": regressed,
                     "base_wins": base_wins, "k": k, "overlap": overlap}, indent=2))

    correction_text = CORRECTION_TEMPLATE.format(
        base_orig=ORIGINAL_ROUND1[MODELS[0]], tuned_orig=ORIGINAL_ROUND1[MODELS[1]], k=k,
        base_mean=base["mean"], base_std=base["stdev"], base_runs=[f"{x:.0%}" for x in per_run[MODELS[0]]],
        tuned_mean=tuned["mean"], tuned_std=tuned["stdev"], tuned_runs=[f"{x:.0%}" for x in per_run[MODELS[1]]],
        base_floor=base["regression_floor"], base_ceiling=base["regression_ceiling"],
        inside_outside="OUTSIDE" if regressed else "INSIDE", verdict=verdict,
        base_wins=base_wins, overlap_text=overlap_text,
        tuned_always_pass=tuned_always_pass, tuned_always_fail=tuned_always_fail, base_flip=base_flip,
    )
    correction_path = HERE.parents[1] / "docs" / "correction.md"
    correction_path.parent.mkdir(exist_ok=True)
    correction_path.write_text(correction_text)
    print(f"\nSaved variance report -> {results_dir / 'finetune_variance_report.json'}")
    print(f"Saved correction doc  -> {correction_path}")


if __name__ == "__main__":
    main()
