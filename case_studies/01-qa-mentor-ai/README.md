# Case Study 01 — QA Mentor AI

A multi-agent RAG assistant for QA automation (myNanoGpt / QA Mentor AI), evaluated
with the method in `../../METHOD.md`.

Every number below is in a committed file under `results/`. To print them all
without a live server or API key: `python3 demo_from_committed.py`.

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

## Out-of-scope handling: `out_of_scope_refused` (Tier 1)

The gap above now has its own **Tier 1 (deterministic)** metric, separate from intent
accuracy: given an off-topic question, does the answer decline or redirect to QA
*without* actually answering the off-topic request? Five goldens
(`goldens/oos_cases.jsonl`: `hard-06`, `hard-07`, plus three new ones: a cookie recipe,
a 2018 World Cup question, an ocean poem), K=3 live runs each, run twice.

| Run | out_of_scope_refused |
|---|---|
| `results/oos_eval_20261001-031805.json` | 13% (2/15) |
| `results/oos_eval_20261001-032004.json` | 27% (4/15) |
| **Both** | **20% (6/30)** |

Per item across both runs: `hard-06` (pizza) 5/6 — usually says the question is
off-topic and pivots to QA content, once ignored it entirely; `oos-01` (cookies) 1/6;
`hard-07` (scraping), `oos-02` (World Cup), `oos-03` (poem) 0/6 — answered in full
every time. All 30 answers routed to `mentor`, so intent accuracy calls every one of
these a pass. This is a real, reported failure; myNanoGpt was not changed to fix it.
Run against myNanoGpt's working tree on 2026-10-01 (commit `b952bc7` plus uncommitted
changes in `agents/`).

How it's scored (`metrics_oos.py`, no LLM): pass = the answer contains a redirect
phrase (off-topic, out of scope, back to QA/testing, can't provide, ...) **and** none
of that golden's hand-picked `off_topic_markers` (e.g. `flour`/`butter` for the recipe,
`France`/`Croatia` for the World Cup). Known risks: a redirect phrased in a way the
regex doesn't list is a false fail, and an off-topic answer that avoids every marker is
a false pass. Hand-reading the first run's answers caught exactly such misses (three
genuine redirects scored as fails), which is why the phrase list was widened and the
saved answers re-scored offline (`python3 run_oos_eval.py --rescore <file>`); every one
of the 30 verdicts above was checked by reading the answer, and the metric flags none of
the 30 in-scope answers in `results/judge_sample.json`.

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

**Human-labelled kappa (in progress).** To remove the controller-as-reference
limitation, 12 of the 30 items are set aside for an independent human rater
(`results/human_labels_subset.json` records which and why: all 4 items the judge
scored below 5, plus 2 per intent). Their scores in
`results/judge_labeling_sheet.csv` are blanked (`label_source = human`) so the rater
isn't anchored by the controller's score; the other 18 rows keep the controller score
(`label_source = controller`). `compute_judge_agreement.py` now computes kappa over the
human rows only and refuses to run until all 12 are filled. Once they are, the human
kappa becomes the primary number here, whatever it says. The controller-reference
result above stays as a secondary, historical number: it's archived in
`results/judge_agreement_report_controller.json`, with the original sheet in
`results/judge_labeling_sheet_controller_backup.csv`.

## Tier 2 — keyword coverage

Keyword coverage on the original 28-question set: **83.2%**, from myNanoGpt's own eval
harness (`evals/results/20260721-023719.json`; recorded in
`results/keyword_coverage_headline.json`, not re-run here). It's a **Tier 2
(reference-based)** proxy: the fraction of each golden's expected keywords that appear
in the answer. It shows whether answers touch the expected concepts. It doesn't show
whether they're correct (`METHOD.md`).

## Metric tiers in this case study

| Metric | Tier | Number |
|---|---|---|
| `intent_accuracy` | 1 — deterministic | 100% (28 and 37 items) |
| `out_of_scope_refused` | 1 — deterministic | 20% (6/30 runs) |
| `keyword_coverage` | 2 — reference-based | 83.2% (28 items) |
| `judge_score` | 3 — judge-based | kappa 0.38 vs controller (WEAK); human kappa pending |

(`TIER_MAP` in `metrics_oos.py`, using `core/metrics.py`'s tier constants.)

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
