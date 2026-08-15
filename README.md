# agent-evals

A method for evaluating non-deterministic agent systems, applied to a system I
built. It caught a result I had originally overstated.

## The method

See [`METHOD.md`](METHOD.md): an N-inputs x K-runs variance harness (tells real
regressions from sampling noise), a judge-agreement check (Cohen's kappa against
human labels, so an LLM judge's trustworthiness is measured, not assumed), and
tiered metrics (deterministic / reference-based / judge-based, so a reader knows
how much to trust each number).

`core/` is written only against one interface, `SystemAdapter` — it never imports
a specific system.

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
  quality (4/13 vs 3/13 compile pass rate, single run each) turned out to be a
  one-example difference with no variance baseline — inside noise. See
  [`docs/correction.md`](docs/correction.md) for the full re-measurement.

## Status

One case study, complete. A second case study (a different agent system, QAthread)
is planned once that system exists — `core/`'s `SystemAdapter` interface is designed
so it plugs in without restructuring anything here.

## Running it

Everything in `core/` is stdlib-only. Anything that calls the live QA Mentor AI
pipeline or the gpt-4o-mini judge needs `myNanoGpt`'s own virtualenv (already has
`requests`, `python-dotenv`, `openai` — not duplicated here):

```bash
cd case_studies/01-qa-mentor-ai
../../../myNanoGpt/.venv/bin/python3 run_hardened_eval.py
```
