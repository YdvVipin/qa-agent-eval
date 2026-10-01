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
  genuine null result (100% before and after I hardened the benchmark); the
  gpt-4o-mini judge is WEAK (kappa 0.38); and a fine-tune "regression" I had
  claimed from single runs didn't survive a K=5 re-measurement.
- **System-agnostic core:** `core/` is stdlib-only and written against one
  interface, `SystemAdapter` — it never imports a specific system.

Reproduce the headline numbers from committed results in one command, no server
or API key: `cd case_studies/01-qa-mentor-ai && python3 demo_from_committed.py`.

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
  as such rather than reframed as a win. (Reading the actual answers during judge
  scoring did surface a real gap the routing metric missed: one adversarial,
  intentionally off-topic question got fully answered instead of redirected back to
  QA topics.)
- Judge reliability: gpt-4o-mini's correctness/completeness judge scored kappa 0.38
  against a 30-item sample — weak, per `METHOD.md`'s own threshold. That sample was
  scored by the controller model directly, not an independently hand-labeled human
  sample; that's a real limitation on this specific number, disclosed here rather
  than glossed over.
- **The correction:** a previous claim that fine-tuning regressed the model's codegen
  quality (4/13 vs 3/13 compile pass rate, single run each) had no variance baseline.
  A K=5 re-run doesn't clear this repo's statistical regression bar, but the base
  model beat the tuned model in all 5 of 5 paired runs with zero overlap between the
  two models' per-run ranges — inconclusive but directionally suggestive, not the
  clean "no difference" the single-run band alone would say. See
  [`docs/correction.md`](docs/correction.md) for the full re-measurement.

## Status

One case study, complete. A second case study is planned against an existing,
architecturally different sibling system (qa-spine, an MCP QA-lifecycle server
that never calls a model itself), via a new `SystemAdapter` with `core/` unchanged.

## Running it

**Fast path (no server, no API key)** — prints the headline numbers from the
committed `results/` files:

```bash
cd case_studies/01-qa-mentor-ai && python3 demo_from_committed.py
```

**Live path** — re-runs against the real system. This assumes a sibling checkout of
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
