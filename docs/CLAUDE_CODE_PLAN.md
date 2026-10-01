# Claude Code implementation plan — agent-evals (post–Phase 1)

> **Audience:** Claude Code (or any agentic implementer). Execute tasks in order.
> Checkboxes (`- [x]`) are the work tracker. Do not re-architect Phase 1.
>
> **Repo:** `/home/vipin-yadav/Desktop/MLProjects/agent-evals`
> **GitHub:** `YdvVipin/qa-agent-eval` (`origin` → `git@github.com:YdvVipin/qa-agent-eval.git`)
> **Sibling system (CS01):** `../myNanoGpt` (QA Mentor AI)
> **Design provenance:** `myNanoGpt/docs/superpowers/specs/2026-08-14-agent-evals-design.md`
> and `.../plans/2026-08-14-agent-evals-phase1.md` (Phase 1 **already shipped**).

**Progress (2026-10-01):** Phases A, B.2, B.3 and C done. B.1 is scaffolded (12-item subset,
`label_source` column, script updated) and waits on Vipin's hand-labels — the open boxes below.

**Goal:** Make this repo outreach-ready: a 90-second hire story, honest credibility
signals (human kappa, Tier-1 graceful-redirect metric, Tier-2 keyword headline), and a
second case study that proves `core/` generalises — without turning the repo into a
product or merging other systems into it.

**Claim (unchanged):** *"Here is a method for evaluating non-deterministic agent
systems. Here it is applied to a system I built. It caught a result I had originally
overstated."* Phase C adds: *"...and the method works on a second, architecturally
different system."*

---

## 0. Current state summary (do not re-do)

Phase 1 (`core/` + case study 01) is **complete and committed**. Treat the following as
ground truth; do not rewrite architecture or re-run the whole Phase 1 plan.

| Area | What exists | Key artefact / number |
|---|---|---|
| `core/` | stdlib-only: `adapter.py`, `variance.py`, `judge_agreement.py`, `metrics.py` | Each has `if __name__ == "__main__": demo()` |
| CS01 adapter | `case_studies/01-qa-mentor-ai/adapter.py` wraps `myNanoGpt/evals/run_evals.py` | Needs live server `:8004` + `myNanoGpt/.venv` |
| Goldens | `original_28.jsonl` + `hard_cases.jsonl` (9 adversarial) | Intent accuracy 100% on both (37-item hardened) |
| Hardened eval | `run_hardened_eval.py` → `results/hardened_eval_20260814-043058.json` | Committed |
| Judge sample | 30 items in `results/judge_sample.json` | gpt-4o-mini scores heavily skewed (26/30 are 5) |
| “Human” labels today | `results/judge_labeling_sheet.csv` column `human_score_1_to_5` | **Controller-model scores, not independent humans** — disclosed in READMEs |
| Kappa | `results/judge_agreement_report.json` | raw 80%, kappa **0.38** (WEAK); controller kappa is secondary |
| Variance (routing) | `run_variance_check.py` → `qa_mentor_variance_check.json` | K=3, 6 items, 18/18 stable |
| Fine-tune correction | `docs/correction.md` + `finetune_variance_report.json` | K=5; not flagged by 2σ band; base won 5/5 paired |
| Docs | `README.md`, `METHOD.md`, CS01 `README.md`, `docs/correction.md` | Hire story exists; needs polish (Phase A) |
| Tier-2 keyword | myNanoGpt harness reports **83.2%** (`evals/results/20260721-023719.json`) | **Not headlined** in CS01 README yet |
| Graceful redirect | `hard-06` / `hard-07` route to `mentor` correctly but answer off-topic | Gap named in CS01 README; **no Tier-1 metric yet** |
| Case study 02 | **Does not exist** | Design deferred QAthread; **QAthread still does not exist — do not invent it** |
| README Status section | Still says “second case study (QAthread) is planned” | Update when Phase C lands (prefer qa-spine) |

### What a hiring manager can already see

Method (variance + kappa + tiers) applied to a real multi-agent RAG system; an honest
correction of an overstated fine-tune claim; `core/` system-agnostic via `SystemAdapter`.

### Known gaps this plan closes

1. Demo friction (live pipeline heavy) and README polish for outreach.
2. Kappa is not yet against true human hand-labels.
3. No Tier-1 metric for out-of-scope refuse / graceful redirect.
4. Tier-2 keyword coverage not headlined.
5. Only one case study — generalisation unproven.

---

## 1. Architecture constraints (non-negotiable)

1. **`core/` stays system-agnostic.** It may import only the stdlib and define/consume
   `SystemAdapter`. Never import `myNanoGpt`, `qa-spine`, QAAE, or any case-study module
   from `core/`.
2. **Case studies talk to systems only through a thin `SystemAdapter`** implementing:
   - `run(self, input: dict) -> dict`
   - `expected_schema(self) -> dict`
   - `intent_of(self, output: dict) -> str | None`
3. **stdlib-only in `core/`.** No numpy, scipy, sklearn, pandas. Kappa stays hand-rolled
   in `judge_agreement.py`.
4. **Reuse, don’t rewrite.** CS01 already reuses `ask_agent` / `keyword_coverage` /
   `llm_judge` from `myNanoGpt/evals/run_evals.py`. Prefer wrapping existing CLIs/APIs
   for CS02.
5. **Separate repos.** Do **not** merge `agent-evals` into `qa-spine`, QAAE, or
   `myNanoGpt`. Sibling checkouts only.
6. **Commit demo artefacts** under each case study’s `results/` so readers can verify
   without a live run when the live path is heavy.
7. **British English** in narrative docs is fine; keep code identifiers American/snake_case
   as today (`cohens_kappa`, `out_of_scope_refused`).

---

## 2. Explicit non-goals (do not do these)

- LangSmith / Ragas / Phoenix clone, hosted eval service, or SaaS.
- Dashboard, rich CLI product, or packaging `agent-evals` as a PyPI framework.
- Merge into `qa-spine`, QAAE, or `myNanoGpt`.
- Add sklearn / numpy / scipy stack.
- Expand the fine-tune holdout beyond 13 items (still a stated limitation in
  `docs/correction.md`; follow-up, not this plan).
- Invent **QAthread** (it does not exist).
- Retrain models, re-run RunPod fine-tunes, or change myNanoGpt agent behaviour as a
  primary deliverable (measuring gaps is in scope; “fix the mentor redirect” in
  myNanoGpt is **out of scope** unless Vipin explicitly asks later).
- Exhaustive eval of all four QA Mentor agents.
- Commit large binaries / secrets / employer data.
- Rewrite Phase 1 `core/` APIs for style alone.

---

## 3. Phase A — Package (P0, 2–3 days)

**Intent:** A stranger (or hiring manager) can understand the repo in ~90 seconds and
reproduce headline numbers from committed results without standing up the full live stack.

### A.1 — README polish (90-second hire story + correction hook)

**Edit:** `README.md`

- [x] **A.1.1** Keep the opening claim; tighten so the first screen answers:
  1. What is the method? (3 tools → link `METHOD.md`)
  2. What did it find on a real system? (routing null result; kappa WEAK; correction)
  3. Where is the honesty artefact? (prominent link to `docs/correction.md`)
- [x] **A.1.2** Add a short **“vs LangSmith / Ragas”** blurb (4–6 lines max). Suggested
  framing (adapt, don’t invent fake feature matrices):
  - LangSmith: tracing / observability product for LLM apps — complementary, not a
    substitute for a variance + kappa method write-up.
  - Ragas: reference-based RAG metrics library — closest to Tier 2; this repo’s point is
    the **tiered trust model + variance protocol + published correction**, not another
    metric pack.
  - This repo is a **method + case studies**, not a platform.
- [x] **A.1.3** Fix the Status line that promises “QAthread”: say case study 02 is
  planned against an **existing** sibling system (qa-spine preferred; see Phase C), via
  a new `SystemAdapter`, with `core/` unchanged. Do not name QAthread as if it exists.
- [x] **A.1.4** Keep the Implementation-plan pointer line if present:
  `Implementation plan for Claude Code: docs/CLAUDE_CODE_PLAN.md`.

**DoD A.1:** A cold reader can state the claim, open `docs/correction.md`, and see how
this differs from LangSmith/Ragas without scrolling past the fold for the correction hook.

### A.2 — One-command / documented demo from committed results

**Add:** `case_studies/01-qa-mentor-ai/demo_from_committed.py` (stdlib only)
**Optionally edit:** `README.md` “Running it” section; CS01 `README.md`

- [x] **A.2.1** Implement a script that **does not** call the live server or OpenAI.
  It must:
  - Load `results/hardened_eval_20260814-043058.json` and print original vs hardened
    intent accuracy.
  - Load `results/judge_agreement_report.json` and print raw agreement, kappa, verdict.
  - Load `results/finetune_variance_report.json` and print base vs tuned mean/stdev,
    `regressed`, `base_wins`.
  - Load `results/qa_mentor_variance_check.json` and print overall mean/stdev.
  - Exit 0 if all files parse and expected keys exist; exit non-zero with a clear error
    otherwise.
- [x] **A.2.2** Document in root `README.md`:
  - **Fast path (no server):**  
    `cd case_studies/01-qa-mentor-ai && python3 demo_from_committed.py`
  - **Live path (unchanged):** myNanoGpt server +  
    `../../../myNanoGpt/.venv/bin/python3 run_hardened_eval.py`
- [x] **A.2.3** Do **not** delete or regenerate committed JSON unless a metric definition
  changes in Phase B (then commit new timestamped files and keep the old ones, or note
  supersession in the CS01 README).

**DoD A.2:** `python3 demo_from_committed.py` works on a clean clone with no
`OPENAI_API_KEY` and no server.

### A.3 — Confirm GitHub presentability (`YdvVipin/qa-agent-eval`)

- [x] **A.3.1** Verify remote: `git remote -v` → `YdvVipin/qa-agent-eval.git`.
- [x] **A.3.2** Confirm tracked set is docs + `core/` + CS01 + committed `results/` only
  (no `__pycache__`, no `.venv`, no large binaries, no `.env`).
- [x] **A.3.3** After A.1–A.2 commits, push `master` (or agreed default branch) so the
  public README matches local. If push needs credentials Vipin must provide, stop after
  local commits and report.
- [x] **A.3.4** Spot-check the GitHub rendering: METHOD link, correction link, CS01 link,
  plan link all resolve.

**DoD A.3:** Public repo README is coherent; clone → `demo_from_committed.py` works.

### Phase A definition of done

- [x] README 90-second story + correction hook + vs LangSmith/Ragas blurb
- [x] Committed-results demo script documented and green
- [x] GitHub `YdvVipin/qa-agent-eval` presentable
- [x] No application behaviour changes in myNanoGpt; no `core/` API break

### Phase A verification

```bash
cd /home/vipin-yadav/Desktop/MLProjects/agent-evals
python3 core/adapter.py
python3 core/variance.py
python3 core/judge_agreement.py
python3 core/metrics.py
cd case_studies/01-qa-mentor-ai && python3 demo_from_committed.py
git status   # only intentional doc/script changes
```

---

## 4. Phase B — Credibility (P1, 3–5 days)

**Intent:** Replace the controller-proxy kappa with a true human sample; add the missing
Tier-1 graceful-redirect metric; headline Tier-2 keyword coverage from the existing
harness.

### B.1 — Human hand-labels (10–15 of 30) and recompute kappa

**Existing files:**
- `results/judge_sample.json` — judge scores (do not overwrite casually)
- `results/judge_labeling_sheet.csv` — columns: `id,question,answer,human_score_1_to_5`
  (currently filled with **controller** scores)
- `compute_judge_agreement.py` — already computes kappa from sheet + sample

**Add / edit:**
- `results/judge_labeling_sheet_controller_backup.csv` (copy of current sheet before edits)
- `results/human_labels_subset.json` (metadata: which ids were human-labelled, date, rater note)
- `results/judge_agreement_report.json` (recomputed; keep prior values in CS01 README history)
- Optionally `results/judge_agreement_report_controller.json` (archive current 0.38 report)
- CS01 `README.md`, root `README.md` (kappa disclosure)

- [x] **B.1.1** Backup the current labelling sheet and the current agreement report under
  clear filenames so controller-vs-human comparison remains auditable.
- [x] **B.1.2** Select **10–15** of the 30 items for true human labels. Prefer diversity:
  include at least one of `hard-06` / `hard-07` if present in the sample ids; mix of
  intents; avoid labelling only the 5/5 cluster. Record the id list in
  `human_labels_subset.json`.
- [ ] **B.1.3** **Vipin (human) fills** `human_score_1_to_5` for those rows only.
  Claude Code must **not** invent human scores. For unlabelled rows either:
  - leave blank and extend `compute_judge_agreement.py` to score **only rows with human
    labels**, or
  - keep controller values but mark them in a new column `label_source` =
    `human` | `controller` and compute kappa on `label_source == human` only.
  Prefer the `label_source` column approach so the CSV stays complete.
- [ ] **B.1.4** Re-run: `python3 compute_judge_agreement.py` (after script update).
  Write new `judge_agreement_report.json` including `n_human`, `cohens_kappa`,
  `raw_agreement`, and a field `reference_rater: "human"`.
- [ ] **B.1.5** Update CS01 README and root README:
  - Primary kappa = **human** subset.
  - Controller kappa 0.38 kept as **secondary** / historical limitation, not deleted.
  - Apply `METHOD.md` thresholds unchanged (&lt;0.4 WEAK, 0.4–0.6 MODERATE, ≥0.6 STRONG).
- [x] **B.1.6** Do not “fix” a low kappa by changing the judge model or rubric silently.
  If human kappa is still WEAK, say so — that is a valid credibility outcome.

**DoD B.1:** Report shows human-labelled n∈[10,15] (or up to 30 if Vipin labels more);
README treats human kappa as primary.

### B.2 — Tier-1 metric: `out_of_scope_refused` / graceful redirect

**Problem (already documented):** `hard-06` and `hard-07` expect intent `mentor` and
**route correctly**, but the mentor fully answers off-topic questions. Routing accuracy
cannot see this gap.

**Add:**
- `case_studies/01-qa-mentor-ai/metrics_oos.py` — deterministic classifiers
- `case_studies/01-qa-mentor-ai/run_oos_eval.py` — score hard-06/hard-07 (and any new OOS
  goldens) from live run **or** from saved answers if committed
- `goldens/oos_cases.jsonl` — start from hard-06/hard-07; optionally add 3–5 more
  clearly off-topic items with the same expected behaviour
- `results/oos_eval_*.json` — committed results
- Tier map note in CS01 README

**Metric definition (implement exactly):**

For each OOS item, given `answer` text (and optionally `routed_intent`):

- **Pass (`out_of_scope_refused` = 1)** if the answer **declines or redirects** to QA /
  testing topics (keywords/phrases such as: cannot help with that, out of scope,
  specialised in QA/testing, try asking about tests/automation, etc.) **and** does not
  provide a substantive how-to for the off-topic request.
- **Fail (= 0)** if the answer provides a usable off-topic solution (scraping guide,
  pizza recommendations as the main content, etc.).

Keep the check **deterministic** (Tier 1): regex / keyword heuristics on the answer are
acceptable; do **not** call an LLM judge for this metric. Document false-positive risk
briefly in CS01 README.

- [x] **B.2.1** Implement `is_graceful_redirect(answer: str) -> bool` with a small unit
  self-check (`demo()`): known redirect snippet → True; hard-07-style scraping guide
  excerpt → False.
- [x] **B.2.2** Implement `run_oos_eval.py`:
  - Default: read answers from the latest hardened results **if** answers were stored;
    today’s `hardened_eval_*.json` rows may **not** include full answers — if missing,
    run live via `QAMentorAdapter` for OOS ids only and commit answers into the OOS
    results JSON.
  - Report per-id pass/fail + rate `out_of_scope_refused`.
- [x] **B.2.3** Headline in CS01 README as **Tier 1**, distinct from intent accuracy.
  Expectation: current system likely **fails** hard-07 (already observed narratively) —
  report the failure honestly; do not change myNanoGpt to green-wash.
- [x] **B.2.4** Register in a local tier_map dict used by the case study docs:
  `out_of_scope_refused` → `TIER_1`, `intent_accuracy` → `TIER_1`,
  `keyword_coverage` → `TIER_2`, `judge_score` → `TIER_3`.

**DoD B.2:** Committed OOS results JSON + README section with the Tier-1 rate; metric is
deterministic and tested.

### B.3 — Headline Tier-2 keyword coverage

**Source of truth already exists:** myNanoGpt
`evals/results/20260721-023719.json` → `summary.keyword_coverage` = **0.832** on the
original 28. Adapter already imports `keyword_coverage`.

- [x] **B.3.1** Either:
  - **Preferred (no live run):** add `results/keyword_coverage_headline.json` that
    records `{ "source": "myNanoGpt/evals/results/20260721-023719.json", "n": 28,
    "keyword_coverage": 0.832, "tier": "reference_based" }` and cite it in CS01 README; or
  - Recompute on `original_28.jsonl` via adapter + `keyword_coverage` if a live server is
    up, and commit the new JSON alongside the citation of the prior harness number.
- [x] **B.3.2** Add a short CS01 README subsection **Tier 2 — keyword coverage** stating
  it is a proxy, not ground truth (`METHOD.md`).
- [x] **B.3.3** Optionally extend `demo_from_committed.py` to print this headline.

**DoD B.3:** CS01 README shows all three tiers with at least one number each.

### Phase B definition of done

- [ ] Human kappa primary (n=10–15+); controller kappa secondary
- [x] `out_of_scope_refused` Tier-1 metric + committed results
- [x] Keyword coverage headlined as Tier 2
- [x] READMEs updated; demo script still green

### Phase B verification

```bash
cd case_studies/01-qa-mentor-ai
python3 metrics_oos.py          # self-check
python3 compute_judge_agreement.py
python3 demo_from_committed.py
# live only if needed for OOS answers:
# ../../../myNanoGpt/.venv/bin/python3 run_oos_eval.py
```

---

## 5. Phase C — Second case study (P2, 5–7 days)

**Intent:** Prove `core/` generalises with a **thin** adapter over an existing sibling
system. Prefer **whichever is easier to drive with deterministic checks**.

### C.0 — System choice (decide once, then lock)

| Candidate | Why it fits | Deterministic hooks | Cost to drive |
|---|---|---|---|
| **qa-spine** (preferred) | Separate repo, MCP QA-lifecycle tools, **server never calls a model**; validates caller output | `audit_submit` rejects bad citations; `release_submit` refuses `ship` while signals live; `gate` exit codes; `npx qa-spine demo`; large existing test suite | Low–medium: Node ≥ 22.5, `npm test` / CLI — no Postgres |
| **QAAE** (`QAAutomationAIEnabler`) | Full ticket→test platform; optional qa-spine integration | Harder: needs Postgres/Redis/Playwright stack; many LLM calls | High |

- [x] **C.0.1** **Default to qa-spine** unless Vipin instructs otherwise. Do **not**
  invent QAthread. Do **not** merge repos.
- [x] **C.0.2** Record the choice in `case_studies/02-qa-spine/README.md` (or
  `02-qaae/` if overridden) opening paragraph.

**Path assumption below:** `case_studies/02-qa-spine/`. If QAAE is chosen, mirror the
same shape under `02-qaae/` and wrap a single deterministic API (e.g. ambiguity-audit
gate), still without modifying `core/`.

### C.1 — Scaffold + thin `SystemAdapter`

**Create:**
```
case_studies/02-qa-spine/
  README.md
  adapter.py
  goldens/
    smoke.jsonl          # 15–25 items
  results/               # committed JSON from the variance/kappa (or deterministic) run
  run_eval.py
  run_variance_or_kappa.py
```

- [x] **C.1.1** Implement `QASpineAdapter` conforming to `SystemAdapter`:
  - `run(input)` invokes a **deterministic** qa-spine path (examples: seed demo store +
    `audit_submit` with fixtures; or `gate` with prepared changed-areas; or
    `fixtures_submit` schema validation). Prefer subprocess CLI / local API already
    used by qa-spine’s own tests over reimplementing store logic.
  - `expected_schema()` documents the output dict (e.g. `accepted: bool`,
    `error_type: str | None`, `detail: dict`).
  - `intent_of(output)` may return a coarse label such as `"accept"` / `"reject"` /
    tool name, or `None` if routing does not apply — that is allowed by the Protocol.
- [x] **C.1.2** `core/` must gain **zero** qa-spine imports. Adapter may live entirely
  under `case_studies/02-qa-spine/`.
- [x] **C.1.3** Self-check: `python3 adapter.py` validates path/CLI availability without
  requiring a long integration run.

**DoD C.1:** `isinstance(QASpineAdapter(), SystemAdapter)` is true conceptually (runtime
checkable Protocol); adapter demo passes.

### C.2 — Goldens (15–25) + one variance **or** kappa run

- [x] **C.2.1** Author `goldens/smoke.jsonl` with 15–25 items. Each line: `id`, input
  payload, `expected` deterministic outcome (accept/reject/exit code). Ground cases in
  real qa-spine rules (unknown rubric rule → reject; quote not in requirement → reject;
  ship without override while blocked → reject; clean audit → accept). **No employer
  data.**
- [x] **C.2.2** `run_eval.py`: run all goldens once; report Tier-1 accuracy; write
  `results/cs02_eval_YYYYMMDD-HHMMSS.json`.
- [x] **C.2.3** Pick **one** of:
  - **Variance:** K≥3 on a subset (≥5 inputs) via `core.variance.run_variance_suite`
    if the path has any nondeterminism; or
  - **Kappa:** if an LLM judge is introduced for a Tier-3 score, run agreement on a
    small labelled set via `core.judge_agreement`.
  For qa-spine’s deterministic validators, **variance of a binary accept/reject will be
  ~0** — that is an acceptable, honest result (stability). Still produce a
  `results/cs02_variance_check.json` (or kappa report) so the method artefacts match CS01.
- [x] **C.2.4** Commit results JSON under `results/`.

**DoD C.2:** 15–25 goldens scored; one variance or kappa artefact committed.

### C.3 — CS02 README + root README status update

- [x] **C.3.1** Write `case_studies/02-qa-spine/README.md`: system one-liner, why it is
  architecturally different from QA Mentor AI (no model calls in-server vs multi-agent
  RAG), metrics table, link to method, pointer that `core/` was reused unchanged.
- [x] **C.3.2** Update root `README.md` Status: **two** case studies; remove QAthread
  language; link CS02.
- [x] **C.3.3** Extend `demo_from_committed.py` pattern: either a sibling
  `case_studies/02-qa-spine/demo_from_committed.py` or a root note listing both demos.

**DoD C.3:** Cold reader sees two case studies and understands generalisation.

### Phase C definition of done

- [x] Thin adapter only; `core/` diff is empty (or docs-only)
- [x] 15–25 goldens + eval results committed
- [x] One variance or kappa run committed
- [x] CS02 README + root Status updated
- [x] Repos not merged; QAthread not created

### Phase C verification

```bash
cd /home/vipin-yadav/Desktop/MLProjects/agent-evals
python3 core/adapter.py && python3 core/variance.py && python3 core/judge_agreement.py
cd case_studies/02-qa-spine
python3 adapter.py
python3 run_eval.py
python3 run_variance_or_kappa.py   # or the chosen script name
python3 demo_from_committed.py     # if added
# Confirm no core imports of qa-spine:
grep -R "qa-spine\|qa_spine" ../../core && echo 'FAIL: core coupled' || echo 'OK'
```

---

## 6. Demo artefacts to leave committed in `results/`

### Case study 01 (already present — keep)

| File | Role |
|---|---|
| `hardened_eval_20260814-043058.json` | Intent accuracy old vs hardened |
| `judge_sample.json` | 30 judged answers |
| `judge_labeling_sheet.csv` | Labels (+ `label_source` after Phase B) |
| `judge_agreement_report.json` | Primary kappa report (human after B) |
| `judge_agreement_report_controller.json` | Archived controller kappa (add in B) |
| `finetune_variance_report.json` | Fine-tune K=5 correction numbers |
| `qa_mentor_variance_check.json` | Routing variance K=3 |
| `keyword_coverage_headline.json` | **Add in B.3** |
| `oos_eval_*.json` | **Add in B.2** |
| `human_labels_subset.json` | **Add in B.1** |

### Case study 02 (add in C)

| File | Role |
|---|---|
| `cs02_eval_*.json` | Golden-set Tier-1 results |
| `cs02_variance_check.json` or `cs02_judge_agreement_report.json` | Method artefact |

### Root / docs

| File | Role |
|---|---|
| `docs/correction.md` | Honesty centrepiece — do not dilute |
| `docs/CLAUDE_CODE_PLAN.md` | This plan |
| `METHOD.md` | System-agnostic method — edit only if thresholds/definitions change |

---

## 7. Order of work (strict)

1. Phase A (package) → push when presentable  
2. Phase B (credibility) — B.1 needs Vipin’s human labelling time; B.2/B.3 can proceed in
   parallel while waiting on labels  
3. Phase C (second case study) — start only after A is done; B may still be finishing
   human labels  

Do not start CS02 scaffolding before A.2’s committed demo exists (outreach baseline first).

---

## 8. Final “done when” checklist (outreach-ready)

- [x] Root README: 90-second hire story, correction hook, vs LangSmith/Ragas, two case
      studies (or CS02 clearly in progress only if C deferred — prefer C complete)
- [x] `python3 case_studies/01-qa-mentor-ai/demo_from_committed.py` green on clean clone
- [ ] Human kappa reported as primary; controller kappa secondary
- [x] Tier-1 `out_of_scope_refused` number published (even if poor)
- [x] Tier-2 keyword coverage headlined
- [x] Tier-3 judge discussed with measured kappa
- [x] `docs/correction.md` intact and linked
- [x] CS02 adapter + 15–25 goldens + one variance/kappa artefact committed
- [x] `core/` still stdlib-only and system-agnostic (`grep` clean of sibling imports)
- [x] GitHub `YdvVipin/qa-agent-eval` matches local mainline docs
- [x] No LangSmith-clone scope creep; no repo merges; no QAthread; no sklearn; no
      holdout expansion; no model retrain

**Hiring-manager test (from original design §7, extended):** In 90 seconds they can
say: this person built an agent system, measured it with a reusable method, knows its
variance, knows when its judge is trustworthy (with **human** agreement), published a
correction about their own work, and showed the method on a **second** system without
rewriting the core.

---

## 9. Commands cheat-sheet

```bash
# core self-checks (always safe)
cd /home/vipin-yadav/Desktop/MLProjects/agent-evals
python3 core/adapter.py
python3 core/variance.py
python3 core/judge_agreement.py
python3 core/metrics.py

# CS01 fast demo (Phase A+)
cd case_studies/01-qa-mentor-ai && python3 demo_from_committed.py

# CS01 live (needs myNanoGpt server on :8004)
cd /home/vipin-yadav/Desktop/MLProjects/myNanoGpt
# uvicorn chat_api:app --host 0.0.0.0 --port 8004
cd ../agent-evals/case_studies/01-qa-mentor-ai
../../../myNanoGpt/.venv/bin/python3 run_hardened_eval.py
../../../myNanoGpt/.venv/bin/python3 run_variance_check.py
../../../myNanoGpt/.venv/bin/python3 run_oos_eval.py          # after B.2

# kappa after human labels
python3 compute_judge_agreement.py

# CS02 (after C.1; qa-spine built/installable)
cd ../02-qa-spine && python3 run_eval.py
```

---

## 10. What Claude Code must ask Vipin (blocking human steps)

1. **Phase B.1:** Hand-label 10–15 scores in the labelling sheet (Claude must not fake
   these).
2. **Phase C.0:** Confirm qa-spine vs QAAE if the default is ever overruled.
3. **GitHub push / secrets:** Any credentialed push or API key use beyond existing local
   `.env` in myNanoGpt.

Everything else in this plan is executable without product-scope decisions.
