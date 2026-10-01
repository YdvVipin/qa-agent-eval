# Case Study 02 — qa-spine

**System choice:** qa-spine, a sibling repo, evaluated with the method in
`../../METHOD.md`. It was picked over QAAutomationAIEnabler because it can be
driven with deterministic checks from its own CLI, with no Postgres, Redis or
Playwright stack to stand up.

qa-spine is an MCP server for the QA lifecycle (requirement → ambiguity findings →
tests → results → release verdict) that **never calls a model itself**. The calling
agent does the reasoning, and qa-spine validates what that agent submits before
recording it. A finding has to cite a real rubric rule and quote the requirement
verbatim. Prose shown to a project manager has to be free of internal jargon. A
release can't ship while a question on a changed requirement is still open, unless
someone named overrides it.

## Why it's a useful second case

| | QA Mentor AI (CS01) | qa-spine (CS02) |
|---|---|---|
| Architecture | Multi-agent RAG; router picks a specialist; LLM writes the answer | Validation server; no model in the server |
| Where non-determinism lives | Inside the system | In the agent calling it, not in qa-spine |
| What's measured | Routing, out-of-scope handling, answer quality, judge trust | Whether it accepts good submissions and rejects bad ones, every time |
| Adapter | HTTP + SSE to a live server (`adapter.py` → myNanoGpt's `run_evals.py`) | Subprocess to qa-spine's CLI (`adapter.py` → `node src/server.ts`) |

`core/` was reused **unchanged**. This case study adds only a new `SystemAdapter`
(`adapter.py`) plus goldens and scripts in this folder. `core/` has no qa-spine imports.

## Results

| Metric | Tier | Result |
|---|---|---|
| Golden accuracy: exit code matches, and the error names the rule when a reject is expected | 1 — deterministic | **100% (25/25)** — `results/cs02_eval_20261001-032544.json` |
| Variance, K=3 on 6 goldens (one per validation path) | — | **mean 1.00, stdev 0.00** (18/18) — `results/cs02_variance_check.json` |

Zero variance is the expected, honest result for a system with no model in the
loop. Here the variance harness confirms stability. In CS01 it measures noise. Either
way it's the same code, run the same way.

The 25 goldens (`goldens/smoke.jsonl`) each start from a fresh store and are grounded
in rules from qa-spine's source and tests. All data is synthetic.

- **Audit** (13): clean submissions accepted, including an empty audit and a
  two-finding batch. Rejected: an unknown rubric rule, a quote not in the requirement,
  a quote whose case differs, a blank quote, internal jargon in a question or
  suggested answer, an out-of-enum confidence, a batch with one bad finding
  (all-or-nothing), an unknown requirement id, and a finding written through the raw
  record path.
- **Release gate** (8): an open question blocks (exit 1). Answering it unblocks
  (exit 0). An unrelated requirement passes. `--record` while blocked records a hold
  and still fails. An override with nobody named is an error (exit 2), and a named
  override ships. An empty store and "nothing to assess" are errors, not passes.
- **Test data** (4): valid locale data is accepted. Rejected: a phone number invalid
  for en-GB, an unknown locale, and a schema keyword the validator doesn't check.

**Correction during authoring:** the first run scored 23/25. Both misses were wrong
goldens, not qa-spine bugs. One assumed an unmatched `--changed` ref is an error;
qa-spine deliberately reports it as uncovered and doesn't block. The other assumed
`pattern` is an unsupported schema keyword; it's supported. Both were corrected
against qa-spine's own tests (`tests/gate.test.ts`, `tests/fixtures.test.ts`) and
re-run. That first results file isn't kept, because it measured my goldens, not
qa-spine.

## Running it

Fast path, no Node or qa-spine checkout needed: `python3 demo_from_committed.py`.

Live: stdlib Python plus a sibling checkout of qa-spine at `../qa-spine` relative to
this repo (override with `QA_SPINE_ROOT`), with `npm install` done and Node ≥ 22.5.
Measured against qa-spine commit `851d15e`.

```bash
cd case_studies/02-qa-spine
python3 adapter.py              # self-check: Protocol conformance + one CLI call
python3 run_eval.py             # 25 goldens, ~13s
python3 run_variance_check.py   # K=3 x 6
```
