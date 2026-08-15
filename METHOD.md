# Method

A system-agnostic way to evaluate non-deterministic agent systems, built around
one interface (`core/adapter.py`'s `SystemAdapter`) and three tools:

## Variance (core/variance.py)

Non-deterministic systems produce different outputs for the same input across
runs. A single before/after comparison can't distinguish a real change from
ordinary sampling noise. The fix: run each input **K times**, compute the
mean and standard deviation of the score, and treat anything within **2 sigma**
of the baseline's own spread as noise, not a regression. `is_regression()`
implements exactly that check.

## Judge agreement (core/judge_agreement.py)

An LLM judge is only as trustworthy as its agreement with a human rater. Raw
agreement overstates reliability when both raters lean toward the same common
label; Cohen's kappa corrects for that by subtracting the agreement expected
by chance. Below kappa 0.4: don't trust the judge as a standalone signal.
0.4-0.6: directionally useful, noisy per-item. Above 0.6: trust it for this
rubric.

## Tiered metrics (core/metrics.py)

Every metric in a case study is labeled by how much it should be trusted:

- **Tier 1 (deterministic):** schema validity, routing correctness — no
  judgment call, unambiguously right or wrong.
- **Tier 2 (reference-based):** keyword/scenario coverage against a known
  reference — a proxy, not ground truth.
- **Tier 3 (judge-based):** LLM-judged quality — only as trustworthy as the
  measured kappa says it is.

## Applying it

A case study implements `SystemAdapter` (`run`, `expected_schema`,
`intent_of`) and nothing else — `core/` never imports a specific system. See
`case_studies/01-qa-mentor-ai/` for the reference implementation.
