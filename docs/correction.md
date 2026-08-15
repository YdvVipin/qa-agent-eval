# Correction: the qa-coder-v2 fine-tune result

**Originally claimed** (round 1, single run each, n=13 holdout):
base `qwen2.5-coder:3b` 4/13 vs. `qa-coder-v2` 3/13 on TypeScript-compile
pass rate — "the fine-tune regressed."

**What a K=5 re-run shows**, same 13-item holdout, Ollama seed varied per run:

| Model | Mean pass rate | Std dev | Per-run |
|---|---|---|---|
| `qwen2.5-coder:3b` (base) | 40.0% | 0.100 | ['54%', '38%', '31%', '46%', '31%'] |
| `qa-coder-v2` (fine-tuned) | 23.1% | 0.000 | ['23%', '23%', '23%', '23%', '23%'] |

**Two ways to read this, and they disagree — stated plainly rather than picking the
more flattering one:**

1. **Single-run noise band** (this repo's chosen regression threshold: mean +/- 2 stdev
   of the base model's own run-to-run spread): [19.9%, 60.1%].
   The tuned model's mean falls **INSIDE** that band. By this test alone,
   no statistically flagged regression.
2. **Paired comparison across the 5 runs**: the base model beat the tuned model in
   5 of 5 runs, with no overlap between the two models' per-run ranges. A sample this small (n=13 holdout
   items, K=5 runs) can't support a confident verdict either way, but a 5/5
   sweep with that pattern is a real directional signal the single-run band is too
   generous to catch.

**Per-item note:** the tuned model's zero stdev is not a rounding artifact — at the
per-item level, `qa-coder-v2` passed the exact same 3 of 13 holdout
items on every one of the 5 seeded runs and failed the exact same 10,
byte-for-byte identical pass/fail pattern regardless of the varied Ollama `seed`. The
base model did not behave this way: 4 of its 13 items flipped between pass
and fail across the 5 runs. So the "0.000 std dev" for the tuned model
reflects zero observed sampling variability across these runs, not just a small measured
number — worth flagging to whoever trains the next version (it may point to the
merged/quantized model being more deterministic, or to `seed` not affecting this
model's output; this pass doesn't try to tell those apart).

**Honest statement:** The single-run noise-band test doesn't flag a statistically significant regression. But the base model won every paired run, with no overlap between the two models' per-run ranges — a real, if statistically underpowered, directional signal that the fine-tune underperforms the base model. Combined with the tuned model's zero per-item variance (above), this is genuinely inconclusive rather than a clean null result: not the confirmed regression originally claimed, and not confidently "no difference" either.

**What did not change:** the mechanism hypothesis — 174 of 263 training records were
GitHub-mined with a prompt ending in a bulleted scenario list, and the model plausibly
learned to continue the list rather than write code. That remains the leading
*hypothesis explaining the absence of gains*, not proof of harm; it wasn't re-tested here.

**Known limitation:** the holdout is 13 items and mirrors the same GitHub-mined
scenario-list format as the training data, so even a real difference of this size may
not be visible here. Expanding to a larger, format-diverse holdout is tracked as
follow-up work, not done in this pass.
