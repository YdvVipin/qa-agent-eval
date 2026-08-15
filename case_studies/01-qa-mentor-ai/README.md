# Case Study 01 — QA Mentor AI

A multi-agent RAG assistant for QA automation (myNanoGpt / QA Mentor AI), evaluated
with the method in `../../METHOD.md`.

## Intent routing: old set vs. hardened set

Intent-routing accuracy is a **Tier 1 (deterministic)** metric per `core/metrics.py`'s
classification — routed correctly or not, no judgment call.

| Set | n | Intent accuracy |
|---|---|---|
| Original golden set | 28 | 100% (28/28) |
| Hardened set (+9 adversarial cases) | 37 | 100% (37/37) |

This is a genuine null result, reported exactly as such: the hardened set did not move
the needle. The original set scored 100% — too easy to discriminate. The 9 added cases
target real boundaries in `agents/router.py`'s routing priority (reviewer > strategy >
testgen > mentor-default): reviewer-vs-strategy, strategy-vs-testgen,
mentor-vs-strategy, one multi-intent case, two out-of-scope cases, and one
reviewer-vs-testgen case. Every one of them still routed correctly against the live
router — no discrimination gained from this batch of adversarial cases. See
`goldens/hard_cases.jsonl` for the rationale on each, and
`results/hardened_eval_20260814-043058.json` for the raw per-case results.

A flat routing-accuracy number isn't the whole story, though. One of the 9 adversarial
cases, `hard-07`, is a fully out-of-scope question ("Can you write me a Python script
to scrape stock prices?") that's *expected* to route to `mentor` as the fallback. It
did route correctly — but the mentor agent then fully answered the off-topic question
(a multi-section guide to scraping stock prices with rotating proxies and Tor) instead
of redirecting the user back to QA topics. Routing accuracy scored this a pass; reading
the actual answer during judge-reliability scoring (below) surfaced it as a real
graceful-degradation gap the metric doesn't catch. The gpt-4o-mini judge scored that
same answer 4/5 ("detailed and helpful"); the controller-model score below scored it
2/5 for being off-topic — a concrete instance of the disagreement discussed next.

## Judge reliability

The judge/kappa numbers in this section are **Tier 3 (judge-based)** per
`core/metrics.py`'s classification — only as trustworthy as the measured agreement
says they are, which is exactly what's being measured here.

30 answers scored by the controller model directly (not an independently hand-labeled
human sample — a real limitation on this specific number, disclosed here rather than
glossed over: the controller is the same kind of model as the judge it's checking, so
correlated LLM biases can't be ruled out the way a genuinely separate human rater would
rule them out), then compared against the gpt-4o-mini judge (same rubric: correctness +
completeness, 1-5).

- Raw agreement: 80% (24/30)
- Cohen's kappa: 0.38
- Verdict: WEAK — judge scores should not be trusted as a standalone quality signal.

Per `METHOD.md`'s thresholds, kappa 0.38 sits just below the 0.4 floor: the
gpt-4o-mini judge's scores track the controller's scores well above chance, but not
well enough to trust in isolation. See `results/judge_agreement_report.json` for the
raw numbers and `results/judge_labeling_sheet.csv` for the per-item scores.

One contributing factor: the judge's own score distribution is heavily skewed — 26 of
30 scores were 5/5 (`results/judge_sample.json`'s `judge_score` field). With marginals
this skewed, raw agreement can look high while kappa stays low almost mechanically
(chance agreement is already high when nearly everyone picks the same label), so this
kappa is at least partly a rubric-discrimination limitation — the 1-5 scale isn't
spreading answers out — not purely a judge-quality one.

Tier 2 (reference-based, e.g. keyword coverage) also exists in the underlying
myNanoGpt eval harness (`evals/run_evals.py`'s `keyword_coverage`) but isn't
separately headlined as a number in this case study pass — worth naming rather than
implying all three tiers are demonstrated here.

## Variance check on QA Mentor AI's own intent routing

The variance harness (`core/variance.py`) was previously only ever exercised against
the separate fine-tune codegen model (see "The fine-tune post-mortem" below), never
against this case study's own system. `run_variance_check.py` closes that gap with a small, live K=3 check: 6 items
(one per intent, plus two boundary cases from the hardened set, `hard-04` and
`hard-09`) run 3 times each against the live pipeline — 18 calls total.

Result: all 6 items routed to the expected intent on all 3 runs (18/18, mean 100%,
stdev 0.000). Routing was stable across this small K=3 sample; this doesn't rule out
variance on a larger sample, it just wasn't observed here — 6 items and 3 runs is a
narrow slice, and the items chosen aren't the hardest cases in the hardened set (those
are covered, unreplicated, in the hardened-eval run above). See
`results/qa_mentor_variance_check.json` for the raw per-item numbers.

## The fine-tune post-mortem

See `../../docs/correction.md` for the full correction. Summary: the original
round-1 claim ("the fine-tune regressed," 4/13 vs 3/13, single run each) was a
one-example difference on n=13 with no variance baseline. A K=5 re-run doesn't
clear this repo's single-run 2-sigma regression bar — the tuned model's mean falls
inside the base model's noise band, so no statistically flagged regression. But the
base model beat the tuned model in all 5 of 5 paired runs, with zero overlap between
the two models' per-run ranges (the tuned model scored a constant 23.1% every run;
the base model's worst run, 30.8%, still exceeds that) — a real, if statistically
underpowered, directional signal. The honest read is inconclusive but directionally
suggestive: not the confirmed regression originally claimed, and not confidently "no
difference" either.
