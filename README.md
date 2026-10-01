# agent-evals

A method for evaluating non-deterministic agent systems, applied to a system I
built. It caught a result I had originally overstated —
**[read the correction](docs/correction.md)**.

- **Method** ([`METHOD.md`](METHOD.md)): an N-inputs x K-runs variance harness
  (real regression or sampling noise?), a judge-agreement check (Cohen's kappa
  against reference labels, so an LLM judge's trustworthiness is measured, not
  assumed), and tiered metrics (deterministic / reference-based / judge-based, so
  you know how much to trust each number).
- **Applied to QA Mentor AI**, a multi-agent RAG system: routing accuracy is a
  genuine null result (100% before and after I hardened the benchmark), but off-topic
  questions are redirected only 20% of the time; the gpt-4o-mini judge is WEAK
  (kappa 0.38); and a fine-tune "regression" I had claimed from single runs
  didn't survive a K=5 re-measurement.
- **Applied to a second, architecturally different system**, qa-spine (a
  validation server with no model inside): 25/25 goldens, zero variance across
  K=3 — with `core/` reused unchanged.
- **System-agnostic core:** `core/` is stdlib-only and written against one
  interface, `SystemAdapter` — it never imports a specific system.

Reproduce the headline numbers from committed results, no server or API key:
`python3 case_studies/01-qa-mentor-ai/demo_from_committed.py` and
`python3 case_studies/02-qa-spine/demo_from_committed.py`.

Implementation plan for Claude Code: [docs/CLAUDE_CODE_PLAN.md](docs/CLAUDE_CODE_PLAN.md).

## How this differs from LangSmith / Ragas

- **LangSmith** is a tracing and observability product for LLM apps. Complementary:
  it shows you what happened on a run, not whether a change between runs is signal
  or noise, or whether your judge can be trusted.
- **Ragas** is a library of reference-based RAG metrics — closest to Tier 2 here.
  This repo's point isn't another metric pack; it's the tiered trust model, the
  variance protocol, and a published correction.
- This is a **method plus case studies**, not a platform.

## Case study 01 — QA Mentor AI

[`case_studies/01-qa-mentor-ai/`](case_studies/01-qa-mentor-ai/README.md) —
a multi-agent RAG QA-automation assistant. Headline findings:

- Intent-routing accuracy: 100% on the original 28-question golden set, and still
  100% on a hardened 37-question set targeting real routing boundaries. A genuine
  null result — I made my own benchmark harder and the score didn't move — reported
  as such rather than reframed as a win.
- Out-of-scope handling — the gap routing accuracy can't see: off-topic questions
  route correctly but then get answered in full. A deterministic Tier 1
  `out_of_scope_refused` metric puts the graceful-redirect rate at **20%** (6/30
  live runs over 5 off-topic questions, K=3, run twice).
- Keyword coverage (Tier 2, reference-based proxy): 83.2% on the original 28.
- Judge reliability: gpt-4o-mini's correctness/completeness judge scored kappa 0.38
  against a 30-item sample — weak, per `METHOD.md`'s own threshold. That sample was
  scored by the controller model directly, not an independently hand-labeled human
  sample; that's a real limitation on this specific number, disclosed here rather
  than glossed over. A 12-item human-labelled subset is set up and waiting on labels;
  its kappa will replace this as the primary number.
- **The correction:** a previous claim that fine-tuning regressed the model's codegen
  quality (4/13 vs 3/13 compile pass rate, single run each) had no variance baseline.
  A K=5 re-run doesn't clear this repo's statistical regression bar, but the base
  model beat the tuned model in all 5 of 5 paired runs with zero overlap between the
  two models' per-run ranges — inconclusive but directionally suggestive, not the
  clean "no difference" the single-run band alone would say. See
  [`docs/correction.md`](docs/correction.md) for the full re-measurement.

## Case study 02 — qa-spine

[`case_studies/02-qa-spine/`](case_studies/02-qa-spine/README.md) — an MCP server
for the QA lifecycle that never calls a model itself. Instead, it validates what a
calling agent submits: findings must cite a real rubric rule and quote the
requirement verbatim, and a release can't ship over an open question unless someone
named overrides it. A new `SystemAdapter` drives qa-spine's own CLI.

- Tier 1 golden accuracy: 100% (25/25) across audit validation, the release gate,
  and test-data validation. Two goldens I'd written wrong on the first pass were
  corrected against qa-spine's own tests, and that's disclosed.
- Variance: K=3 on 6 goldens, stdev 0.00. That's the expected result for a server
  with no model in it, measured rather than assumed, using the same `core/variance.py`
  that measures noise in CS01.

## Status

Two case studies, both complete. `core/` was not modified to add the second one.
Pending: human labels for the 12-item kappa subset in case study 01.

## Running it

**Fast path (no server, no API key)** — prints the headline numbers from the
committed `results/` files:

```bash
python3 case_studies/01-qa-mentor-ai/demo_from_committed.py
python3 case_studies/02-qa-spine/demo_from_committed.py
```

Case study 02 live: see its [README](case_studies/02-qa-spine/README.md#running-it)
(sibling qa-spine checkout, Node ≥ 22.5, stdlib Python).

**Case study 01 live path** — re-runs against the real system. This assumes a sibling checkout of
`myNanoGpt` (the QA Mentor AI system being evaluated) at `../myNanoGpt` relative to
this repo, with its own server running (`uvicorn chat_api:app --host 0.0.0.0 --port
8004` from within that repo) and an `OPENAI_API_KEY` in its `.env` for the judge
calls.

Everything in `core/` is stdlib-only. Anything that calls the live QA Mentor AI
pipeline or the gpt-4o-mini judge needs `myNanoGpt`'s own virtualenv (already has
`requests`, `python-dotenv`, `openai` — not duplicated here):

```bash
cd case_studies/01-qa-mentor-ai
../../../myNanoGpt/.venv/bin/python3 run_hardened_eval.py
```
