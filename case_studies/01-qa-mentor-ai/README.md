# Case Study 01 — QA Mentor AI

A multi-agent RAG assistant for QA automation (myNanoGpt / QA Mentor AI), evaluated
with the method in `../../METHOD.md`.

## Intent routing: old set vs. hardened set

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
`hard_cases.jsonl` for the rationale on each, and `results/hardened_eval_20260814-043058.json`
for the raw per-case results.

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

## The fine-tune post-mortem

See `../../docs/correction.md` for the full correction. Summary: the original
round-1 claim ("the fine-tune regressed," 4/13 vs 3/13, single run each) was a
one-example difference on n=13 with no variance baseline — inside noise. A K=5
re-run puts real numbers on that noise band and restates the verdict honestly.
