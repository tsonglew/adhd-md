I'll start by reading the skill snapshot and the input document.

Now let me read the required reference files and check the skill's scripts.

Let me check the prompt file and run the audit.

The examples include an English runbook pair — directly relevant. Let me read it.

I have what I need. Now writing the content-scope rewrite (structure preserved: same H1/H2 levels, same list forms, no new emphasis or block types).

Verify passes with no warnings or unknowns. Let me refine two spots — the opening sentence load and the step-5 split — then re-check.

All checks are green. Here's the report.

## Report: `input.md` → `output.md`

**scope** `content` · **level** `standard` · written to `output.md` (input.md untouched). `fmt --write` was skipped, as the skill prescribes for `scope=content`.

### Script score (not the final score)

| Dimension | before | after | delta |
|---|---|---|---|
| First-screen conclusion | 100.0 | 100.0 | +0.0 |
| Chunk granularity | 100.0 | 100.0 | +0.0 |
| Scannability | 100.0 | 100.0 | +0.0 |
| Sentence load | 100.0 | 100.0 | +0.0 |
| Actionability | 100.0 | 100.0 | +0.0 |
| Typographic consistency | 100.0 | 100.0 | +0.0 |
| Human feel | 100.0 | 100.0 | +0.0 |

**Script score 100.0 → 100.0 (+0.0).** The `band` is `null`: this is the script score only, with 23 rules unjudged. The input already passed every script-checked rule, so the gain in this rewrite lives entirely in the model-judged column.

**Anti-pattern (X) deductions: −0 → −0** (`x_hits` empty). X4 (deleted information) did not fire — nothing was removed. No emoji, no fragmentation, no bold, no tables, no folding.

### verify status

**`verify --scope=content`: `pass`** — `hard_failures: []`, `warnings: []`, `unknowns: []`, `ok: true`. Stated precisely: this means the declared machine checks passed (code blocks, link targets, inline-code values, numbers/units, identifiers, frontmatter) with nothing left for manual review. It is not a semantic-equivalence proof, and I am not reporting any `unknown` as a pass — there were none.

### What I changed (content only)

- **Conclusion-first opening** (output.md:3): the doc now leads with the symptom ("A record changed more than 5 minutes ago, but the dashboard still shows its previous value. The primary database already has the new value.") plus the plan. It previously opened with the scope/meta line.
- **Headings carry their answer** (output.md:7,17): `Confirm the issue: 3 checks`, `Recovery: 5 steps`.
- **Progress markers** (output.md:21–25): `Step X of 5` on every recovery step.
- **Compound actions split inside their existing list items**: step 2 (check queue depth / save the value), step 3 (wait 3 minutes / refresh once — the "queue is nonzero" condition still governs both), step 5 (confirm / close, order preserved).
- **`All three must be true:`** added as the lead-in to the three confirmation checks — the conjunction was implicit; no new condition was introduced.
- **Two constraints moved above the steps** (output.md:19): "Do not rebuild the global index during business hours. Requeueing does not modify the primary database." now precede the procedure (read before acting) and the section ends on a closing action.
- **Preserved verbatim or in substance**: 5 minutes, 3 minutes, `workspace ID`, `record ID`, `last update time`, `indexer queue depth`, `metric value`, "nonzero", "requeue **only** the affected workspace", the write-failure runbook exception, the scope exclusions (billing exports, direct database queries), and both closing negations. No code blocks or links existed; none were added.

### Deliberately not changed

- **No `<details>` folding, no `---` divider, no `> **Warning**` label, no bold, no inline-code backticks, no new headings or list items, no TOC** — every one of these is a format-axis move (N3/N4/T3/T5), and `scope=content` forbids touching typography, block types, emphasis markers, and list form. The N3 advisory fires identically before and after and is left as-is for the same reason.
- **No minute estimate** — only countable length ("3 checks", "5 steps"). Minutes would be invented.
- **Steps 3 and 4 keep their condition first**; converting them to bare commands would break the branch.

### Unjudged rules (all 23 are unscored by the script — the 100 does not cover them)

Verdicts below are the model pass the skill requires; a script score cannot substitute for this table.

| Rule | Verdict | Evidence / reason |
|---|---|---|
| S4 headings state conclusions | met | output.md:7,17 — count + deliverable in each heading, not a bare topic |
| S5 conclusion up front | met | output.md:3 — symptom and plan in the first 3 lines |
| H4 time/length estimate | met | "3 checks … 5 steps" (output.md:3), reinforced by both headings; no invented minutes |
| P2 one topic per paragraph | met | TL;DR / scope / gate / exception / cautions are separate single-purpose paragraphs |
| P5 long quote block | N/A | no blockquote blocks |
| L2 enumerable prose → list | N/A | both enumerable sets already are lists; none left in prose |
| L4 parallel list items | met (caveat) | bullets all subject-first present tense; steps 3–4 open with their condition by necessity |
| L7 items keep full meaning | met | every item is a full clause; verified by reading items standalone |
| W2 active voice | met | no true passives; "is visible" / "is in progress" are stative |
| W3 parenthetical >5 words | N/A | no parenthetical insertions |
| W5 explain terms at first use | N/A | no abbreviations introduced; `ID` is in the skill's common-acronym allowlist |
| W8 one clause per sentence | met | heaviest sentence carries a single "but" |
| A1 section ends with a next step | met | output.md:15 (write-failure handoff), output.md:25 ("Then close the incident.") |
| **A7 expected output / verification** | **not met — 2 of 5 steps** | steps 3–4 use the source's own conditions as checks and step 5 is an explicit confirm; steps 1–2 have no documented observable in the source — left as a source gap rather than invented |
| **A8 one action per step** | **not met (scope limitation)** | steps 2, 3, 5 still carry two actions under one number; sentences are split inside the item, but making one number = one action would require new list items, which `scope=content` forbids |
| N7 progress on ≥4-step flow | met | `Step X of 5` on all five steps (output.md:21–25) |
| T3 consistent markers | N/A | no bold/italic/code emphasis used anywhere, so nothing can be mixed |
| C4 (Chinese modifier order) | N/A | document language is `en` |
| X3 fragments instead of sentences | not hit | no item lost subject or predicate |
| X6 table abuse | not hit | no tables |
| X7 collapse abuse | not hit | no `<details>`; nothing on the main path is hidden |
| X8 template boilerplate | not hit | two sections with distinct content, no repeated empty subheads |

Hint-only rules (no score): C7 and M10 are Chinese-only, M2 not triggered. One advisory finding (N3, no divider between the two H2 sections) exists identically in before and after; not actioned, as it is a format change outside `scope=content`.

All checks are green. Here's the report.

## Report: `input.md` → `output.md`

**scope** `content` · **level** `standard` · written to `output.md` (input.md untouched). `fmt --write` was skipped, as the skill prescribes for `scope=content`.

### Script score (not the final score)

| Dimension | before | after | delta |
|---|---|---|---|
| First-screen conclusion | 100.0 | 100.0 | +0.0 |
| Chunk granularity | 100.0 | 100.0 | +0.0 |
| Scannability | 100.0 | 100.0 | +0.0 |
| Sentence load | 100.0 | 100.0 | +0.0 |
| Actionability | 100.0 | 100.0 | +0.0 |
| Typographic consistency | 100.0 | 100.0 | +0.0 |
| Human feel | 100.0 | 100.0 | +0.0 |

**Script score 100.0 → 100.0 (+0.0).** The `band` is `null`: this is the script score only, with 23 rules unjudged. The input already passed every script-checked rule, so the gain in this rewrite lives entirely in the model-judged column.

**Anti-pattern (X) deductions: −0 → −0** (`x_hits` empty). X4 (deleted information) did not fire — nothing was removed. No emoji, no fragmentation, no bold, no tables, no folding.

### verify status

**`verify --scope=content`: `pass`** — `hard_failures: []`, `warnings: []`, `unknowns: []`, `ok: true`. Stated precisely: this means the declared machine checks passed (code blocks, link targets, inline-code values, numbers/units, identifiers, frontmatter) with nothing left for manual review. It is not a semantic-equivalence proof, and I am not reporting any `unknown` as a pass — there were none.

### What I changed (content only)

- **Conclusion-first opening** (output.md:3): the doc now leads with the symptom ("A record changed more than 5 minutes ago, but the dashboard still shows its previous value. The primary database already has the new value.") plus the plan. It previously opened with the scope/meta line.
- **Headings carry their answer** (output.md:7,17): `Confirm the issue: 3 checks`, `Recovery: 5 steps`.
- **Progress markers** (output.md:21–25): `Step X of 5` on every recovery step.
- **Compound actions split inside their existing list items**: step 2 (check queue depth / save the value), step 3 (wait 3 minutes / refresh once — the "queue is nonzero" condition still governs both), step 5 (confirm / close, order preserved).
- **`All three must be true:`** added as the lead-in to the three confirmation checks — the conjunction was implicit; no new condition was introduced.
- **Two constraints moved above the steps** (output.md:19): "Do not rebuild the global index during business hours. Requeueing does not modify the primary database." now precede the procedure (read before acting) and the section ends on a closing action.
- **Preserved verbatim or in substance**: 5 minutes, 3 minutes, `workspace ID`, `record ID`, `last update time`, `indexer queue depth`, `metric value`, "nonzero", "requeue **only** the affected workspace", the write-failure runbook exception, the scope exclusions (billing exports, direct database queries), and both closing negations. No code blocks or links existed; none were added.

### Deliberately not changed

- **No `<details>` folding, no `---` divider, no `> **Warning**` label, no bold, no inline-code backticks, no new headings or list items, no TOC** — every one of these is a format-axis move (N3/N4/T3/T5), and `scope=content` forbids touching typography, block types, emphasis markers, and list form. The N3 advisory fires identically before and after and is left as-is for the same reason.
- **No minute estimate** — only countable length ("3 checks", "5 steps"). Minutes would be invented.
- **Steps 3 and 4 keep their condition first**; converting them to bare commands would break the branch.

### Unjudged rules (all 23 are unscored by the script — the 100 does not cover them)

Verdicts below are the model pass the skill requires; a script score cannot substitute for this table.

| Rule | Verdict | Evidence / reason |
|---|---|---|
| S4 headings state conclusions | met | output.md:7,17 — count + deliverable in each heading, not a bare topic |
| S5 conclusion up front | met | output.md:3 — symptom and plan in the first 3 lines |
| H4 time/length estimate | met | "3 checks … 5 steps" (output.md:3), reinforced by both headings; no invented minutes |
| P2 one topic per paragraph | met | TL;DR / scope / gate / exception / cautions are separate single-purpose paragraphs |
| P5 long quote block | N/A | no blockquote blocks |
| L2 enumerable prose → list | N/A | both enumerable sets already are lists; none left in prose |
| L4 parallel list items | met (caveat) | bullets all subject-first present tense; steps 3–4 open with their condition by necessity |
| L7 items keep full meaning | met | every item is a full clause; verified by reading items standalone |
| W2 active voice | met | no true passives; "is visible" / "is in progress" are stative |
| W3 parenthetical >5 words | N/A | no parenthetical insertions |
| W5 explain terms at first use | N/A | no abbreviations introduced; `ID` is in the skill's common-acronym allowlist |
| W8 one clause per sentence | met | heaviest sentence carries a single "but" |
| A1 section ends with a next step | met | output.md:15 (write-failure handoff), output.md:25 ("Then close the incident.") |
| **A7 expected output / verification** | **not met — 2 of 5 steps** | steps 3–4 use the source's own conditions as checks and step 5 is an explicit confirm; steps 1–2 have no documented observable in the source — left as a source gap rather than invented |
| **A8 one action per step** | **not met (scope limitation)** | steps 2, 3, 5 still carry two actions under one number; sentences are split inside the item, but making one number = one action would require new list items, which `scope=content` forbids |
| N7 progress on ≥4-step flow | met | `Step X of 5` on all five steps (output.md:21–25) |
| T3 consistent markers | N/A | no bold/italic/code emphasis used anywhere, so nothing can be mixed |
| C4 (Chinese modifier order) | N/A | document language is `en` |
| X3 fragments instead of sentences | not hit | no item lost subject or predicate |
| X6 table abuse | not hit | no tables |
| X7 collapse abuse | not hit | no `<details>`; nothing on the main path is hidden |
| X8 template boilerplate | not hit | two sections with distinct content, no repeated empty subheads |

Hint-only rules (no score): C7 and M10 are Chinese-only, M2 not triggered. One advisory finding (N3, no divider between the two H2 sections) exists identically in before and after; not actioned, as it is a format change outside `scope=content`.
