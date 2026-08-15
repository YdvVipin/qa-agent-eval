# Correction: the qa-coder-v2 fine-tune result

**Originally claimed** (round 1, single run each, n=13 holdout):
base `qwen2.5-coder:3b` 4/13 vs. `qa-coder-v2` 3/13 on TypeScript-compile
pass rate — "the fine-tune regressed."

**What a K=5 re-run shows**, same 13-item holdout, Ollama seed varied per run:

| Model | Mean pass rate | Std dev | Per-run |
|---|---|---|---|
| `qwen2.5-coder:3b` (base) | 40.0% | 0.100 | ['54%', '38%', '31%', '46%', '31%'] |
| `qa-coder-v2` (fine-tuned) | 23.1% | 0.000 | ['23%', '23%', '23%', '23%', '23%'] |

The base model's 2-sigma band is [19.9%, 60.1%]. The tuned
model's mean falls **INSIDE** that band.

**Per-item note:** the tuned model's zero stdev is not a rounding artifact —
at the per-item level, `qa-coder-v2` passed the exact same 3 of 13 holdout items
on every one of the 5 seeded runs and failed the exact same 10, byte-for-byte
identical pass/fail pattern regardless of the varied Ollama `seed`. The base
model did not behave this way: 4 of its 13 items flipped between pass and fail
across the 5 runs. So the "0.000 std dev" for the tuned model reflects zero
observed sampling variability across these runs, not just a small measured
number — worth flagging to whoever trains the next version (it may point to
the merged/quantized model being more deterministic, or to `seed` not
affecting this model's output; this pass doesn't try to tell those apart).

**Honest statement:** No measurable improvement or regression from the base model, given the measured variance — the original single-run comparison was inside noise.

**What did not change:** the mechanism hypothesis — 174 of 263 training records were
GitHub-mined with a prompt ending in a bulleted scenario list, and the model plausibly
learned to continue the list rather than write code. That remains the leading
*hypothesis explaining the absence of gains*, not proof of harm; it wasn't re-tested here.

**Known limitation:** the holdout is 13 items and mirrors the same GitHub-mined
scenario-list format as the training data, so even a real difference of this size may
not be visible here. Expanding to a larger, format-diverse holdout is tracked as
follow-up work, not done in this pass.
