I'll start by reading the skill and the input file.

## Delivered: `output.md` — scope `format` · level `deep` (3)

`input.md` is untouched (631 bytes, mtime unchanged); `output.md` is written in the same directory.

**Bottom line: this document needed no reformatting.** `fmt` reports "格式已规范，无需修改", and every format-scope edit I could construct for it would have deleted original characters or reordered information — both forbidden by this case. So `output.md` is a **byte-identical copy** of `input.md` (SHA-256 `ed563572dd10b7cf…`, 631 bytes each, both ending in a single newline). That is the deliverable, not an oversight; the reasoning is below.

### Machine evidence (all runs at this case's `--level 3 --scope=format`)

| command | exit | result |
|---|---|---|
| `audit input.md --level 3 --scope=format` | **0** | script score **97.4** / 100 · 1 finding (`T2d`) |
| `audit output.md --level 3 --scope=format` | **0** | script score **97.4** / 100 · same 1 finding |
| `verify input.md output.md --scope=format` | **0** | `status: "pass"`, `ok: true`, `identical: true`, `hard_failures: []`, `warnings: []`, `unknowns: []` |
| `report input.md output.md --scope=format --level 3` | **0** | 97.4 → 97.4 (+0.0) · anti-pattern −0 → −0 · findings 1 → 1 |
| `fmt input.md` (preview) | 0 | "格式已规范，无需修改" |

**Script score before → after, by dimension** (script score only — not a final score; 32 judge rules are counted as not-hit and are judged by hand below):

| dimension | before | after | delta |
|---|---|---|---|
| 首屏结论力 (hook) | 100.0 | 100.0 | +0.0 |
| 分块粒度 (chunking) | 100.0 | 100.0 | +0.0 |
| 扫读性 (scannability) | 100.0 | 100.0 | +0.0 |
| 句子负荷 (sentence load) | 100.0 | 100.0 | +0.0 |
| 行动性 (actionability) | 100.0 | 100.0 | +0.0 |
| 排版一致性 (typography) | 80.0 | 80.0 | +0.0 |
| 活人感 (human feel) | 100.0 | 100.0 | +0.0 |

### `verify --scope=format`: **pass (exit 0)** — and what that does and does not mean

Three-state result: `pass`, **not** `unknown` (exit 4) and **not** `fail` (exit 3). No unknowns were emitted, so nothing here is being reported as a pass that was actually undetermined. But the pass is a *zero-diff* pass: the validator saw `old == new`, set `identical: true` and returned immediately. It therefore proves the delivered file is identical to the source — it is **not** an equivalence proof for any rewrite, because no rewrite was attempted. Checks that would have run on a real diff (code-block bodies, link targets, frontmatter, inline literals, numbers/units, prose token multiset) were not exercised.

### Anti-pattern (X group) deductions: **0** before, **0** after

`x_deduct: 0`, `x_hits: {}`. Specifically: X1 zero emoji · X2 one heading over 30 lines · X5 bold density 8.3% (X5 only fires above 12%). No X-group deduction is being hidden behind the `pass`.

### Unjudged rules — coverage: 41 applicable · 23 script-checked · 5 hint-only · 10 judge-only (in scope) · 2 auto-fix · 1 hard gate. 32 judge rules total are unscored by the script.

**In-scope judge rules (F axis, 10):**

| rule | verdict | basis |
|---|---|---|
| S5 conclusion-first | n/a | No conclusion/answer block exists. The only candidate is the warning quote (L10–12); the case also requires preserving information order. |
| S6 doc-type skeleton | n/a | Matches none of the six skeletons in `doc-types.md`; reordering barred by the case. |
| P2 one topic per paragraph | met | L8, L10–12, L14–17, L30 are each single-topic; L19–22 is a field/value table. |
| P5 long quote block | met | Quote is 3 lines (threshold is >5). |
| L2 enumerable clauses → list | not met (kept as prose) | L30's two parallel sentences could be listified, but that deletes the sentence-final periods (characters) and cuts the "too" back-reference. Unscored; listed under "deliberately not changed". |
| N4 fold optional content | n/a | Nothing off the main path to fold; folding main-path steps would hit X7, and injected HTML would drive `verify` to `unknown`. |
| T3 marker semantics consistent | met | Bold = step keyword / contrastive emphasis (L14, L30); inline code = literals (L8, L15, L16, L21, L22); no italics. |
| X3 keyword-fragment list items | clear | Every list item is a self-contained sentence. |
| X6 table misuse | clear | L19–22 is homogeneous field/value pairs with short cells. |
| X7 fold misuse | clear | No `<details>` in the document. |
| X8 boilerplate template | clear | No repeated mini-heading shell; a single H1. |

**Out-of-scope judge rules (C axis, 22) — recorded, not silently passed:**

| rule | verdict | basis |
|---|---|---|
| S4 conclusion-style heading | n/a | Rewording a heading is content; blocked by `scope=format`. |
| S8 section-opening sentence | n/a | Content axis; document has one H1 and no subsections. |
| H3 first-screen reader benefit | not met (scope) | Would require a new sentence; L6–L8 state no reader benefit. |
| H4 time/length estimate | not met (scope) | No "约 N 分钟 / 共 N 步" on the first screen; adding one is content. |
| L4 parallel list items | met | L14/L17 both imperative verb-initial; L15/L16 both "Confirm …". |
| L7 list items keep full meaning | met | All four items carry subject + verb and stand alone. |
| W2, W3, W5, W7, W8 | n/a | `rules.md`: the entire W group is inert under `scope=format`. |
| W9 negative → positive | n/a (exception anyway) | W group inert; note L12's negative phrasing sits in a warning, which W9 exempts. |
| A1 section-ending next step | n/a | Content axis; no H2 sections, and L17 is already an explicit action. |
| A2 per-step time estimate | not met (scope) | L14/L17 carry no estimates; adding them is content. |
| A3 default recommendation | n/a | No multi-option choice anywhere. |
| A5 "if you do one thing" | n/a | Content axis; 30-line document, not a long-doc first screen. |
| A6 decision-point criteria | n/a | No decision point ("only after approval" is a condition, not a fork). |
| **A7 expected output / verification** | **not met** | Neither step (L14, L17) shows what success looks like. The source states no output, exit state, or check to reuse, so this stays unmet by design — I did not invent output to close it. |
| **A8 one action per step** | **met** | L14 and L17 each hold one action; L15/L16 are separate confirmations. The approval clause on L17 is a branch, not a compound action. |
| **N7 progress marking (≥4 steps)** | **n/a** | The flow has 2 steps; the rule deliberately stays silent below 4. |
| C4 Chinese modifier order | n/a | CJK-only rule; document language is `en`. |

**Hint-only rules (no score effect):** S7 (>600 lines — n/a), L6 (>7 items — n/a), N3 (divider between H2s — no H2s), T5 (canonical warning label — the existing quote carries no 注意/警告 prefix, and adding one would be new wording), C6 (Chinese list punctuation — n/a).

### What I changed

**Nothing.** Every format-scope operation available against this document was tested against the case's constraints and rejected: there is no paragraph over the limits, no missing blank line, no missing fence language, no nesting to flatten, no heading level to fix, no TOC trigger (30 lines < 80), no token to reorder, and no optional branch worth folding. `fmt` independently reports the file as already canonical. Writing a "reformat" that only churns the file would have risked the boundary constructs this document exists to carry.

### What I deliberately did not change

- **The bold in `**Preview**`, `**first copy**`, `**second copy**` (L14, L30).** This is the sole deduction — `T2d`, bold density 8.3% vs the 8% cap, anchored at `output.md:1` because it is a document-level ratio over prose blocks; the contributing spans are L14 and L30. I verified the fix works and that the gate would *not* have stopped it: removing just the four `*` characters around `Preview` raises the script score to **100.0** and `verify` still returns pass. I declined anyway — this case requires preserving every original character, deleting the author's emphasis to satisfy a ratio is metric-gaming, and 8.3% is an artifact of a ~313-character prose body with 26 bold characters. `X5` (12% cap) is clear, so this is a T-axis deduction, not an anti-pattern.
- **The two `x ** 2`, `A->B` code spans, the `route /v2/items -> cache` block, the `?region=west#step-2` link target, `15 s` and `0`, and the YAML frontmatter** — all preserved verbatim; frontmatter is character-protected under `format`.
- **The repeated terms at L30.** Both copies stay ("retain the **first copy**. Retain the **second copy** too."). Repetition here is the fixture's point; nothing was deduplicated.
- **The warning text (L10–12).** Kept word-for-word, and it was not rewritten into new phrasing or moved to the top.
- **Information order.** Unchanged end to end — `S5`/`S6`-style block moves are off the table for this case.
- **No TL;DR, no emoji, no `<details>`, no new headings, no added time estimate or next-step line.** All of those are content operations, and the folding option would also have flipped `verify` to `unknown`.

### Target status: partial — stated as such

The anti-pattern requirement is met (X group = 0). The stronger target "no script deductions" is **not met**: one hit remains, `T2d` bold density 8.3% > 8% at `output.md:1`. It is clearable only by deleting original `*` characters, which this case forbids, so I kept the source text and am reporting the residual rather than editing around the metric.

## Delivered: `output.md` — scope `format` · level `deep` (3)

`input.md` is untouched (631 bytes, mtime unchanged); `output.md` is written in the same directory.

**Bottom line: this document needed no reformatting.** `fmt` reports "格式已规范，无需修改", and every format-scope edit I could construct for it would have deleted original characters or reordered information — both forbidden by this case. So `output.md` is a **byte-identical copy** of `input.md` (SHA-256 `ed563572dd10b7cf…`, 631 bytes each, both ending in a single newline). That is the deliverable, not an oversight; the reasoning is below.

### Machine evidence (all runs at this case's `--level 3 --scope=format`)

| command | exit | result |
|---|---|---|
| `audit input.md --level 3 --scope=format` | **0** | script score **97.4** / 100 · 1 finding (`T2d`) |
| `audit output.md --level 3 --scope=format` | **0** | script score **97.4** / 100 · same 1 finding |
| `verify input.md output.md --scope=format` | **0** | `status: "pass"`, `ok: true`, `identical: true`, `hard_failures: []`, `warnings: []`, `unknowns: []` |
| `report input.md output.md --scope=format --level 3` | **0** | 97.4 → 97.4 (+0.0) · anti-pattern −0 → −0 · findings 1 → 1 |
| `fmt input.md` (preview) | 0 | "格式已规范，无需修改" |

**Script score before → after, by dimension** (script score only — not a final score; 32 judge rules are counted as not-hit and are judged by hand below):

| dimension | before | after | delta |
|---|---|---|---|
| 首屏结论力 (hook) | 100.0 | 100.0 | +0.0 |
| 分块粒度 (chunking) | 100.0 | 100.0 | +0.0 |
| 扫读性 (scannability) | 100.0 | 100.0 | +0.0 |
| 句子负荷 (sentence load) | 100.0 | 100.0 | +0.0 |
| 行动性 (actionability) | 100.0 | 100.0 | +0.0 |
| 排版一致性 (typography) | 80.0 | 80.0 | +0.0 |
| 活人感 (human feel) | 100.0 | 100.0 | +0.0 |

### `verify --scope=format`: **pass (exit 0)** — and what that does and does not mean

Three-state result: `pass`, **not** `unknown` (exit 4) and **not** `fail` (exit 3). No unknowns were emitted, so nothing here is being reported as a pass that was actually undetermined. But the pass is a *zero-diff* pass: the validator saw `old == new`, set `identical: true` and returned immediately. It therefore proves the delivered file is identical to the source — it is **not** an equivalence proof for any rewrite, because no rewrite was attempted. Checks that would have run on a real diff (code-block bodies, link targets, frontmatter, inline literals, numbers/units, prose token multiset) were not exercised.

### Anti-pattern (X group) deductions: **0** before, **0** after

`x_deduct: 0`, `x_hits: {}`. Specifically: X1 zero emoji · X2 one heading over 30 lines · X5 bold density 8.3% (X5 only fires above 12%). No X-group deduction is being hidden behind the `pass`.

### Unjudged rules — coverage: 41 applicable · 23 script-checked · 5 hint-only · 10 judge-only (in scope) · 2 auto-fix · 1 hard gate. 32 judge rules total are unscored by the script.

**In-scope judge rules (F axis, 10):**

| rule | verdict | basis |
|---|---|---|
| S5 conclusion-first | n/a | No conclusion/answer block exists. The only candidate is the warning quote (L10–12); the case also requires preserving information order. |
| S6 doc-type skeleton | n/a | Matches none of the six skeletons in `doc-types.md`; reordering barred by the case. |
| P2 one topic per paragraph | met | L8, L10–12, L14–17, L30 are each single-topic; L19–22 is a field/value table. |
| P5 long quote block | met | Quote is 3 lines (threshold is >5). |
| L2 enumerable clauses → list | not met (kept as prose) | L30's two parallel sentences could be listified, but that deletes the sentence-final periods (characters) and cuts the "too" back-reference. Unscored; listed under "deliberately not changed". |
| N4 fold optional content | n/a | Nothing off the main path to fold; folding main-path steps would hit X7, and injected HTML would drive `verify` to `unknown`. |
| T3 marker semantics consistent | met | Bold = step keyword / contrastive emphasis (L14, L30); inline code = literals (L8, L15, L16, L21, L22); no italics. |
| X3 keyword-fragment list items | clear | Every list item is a self-contained sentence. |
| X6 table misuse | clear | L19–22 is homogeneous field/value pairs with short cells. |
| X7 fold misuse | clear | No `<details>` in the document. |
| X8 boilerplate template | clear | No repeated mini-heading shell; a single H1. |

**Out-of-scope judge rules (C axis, 22) — recorded, not silently passed:**

| rule | verdict | basis |
|---|---|---|
| S4 conclusion-style heading | n/a | Rewording a heading is content; blocked by `scope=format`. |
| S8 section-opening sentence | n/a | Content axis; document has one H1 and no subsections. |
| H3 first-screen reader benefit | not met (scope) | Would require a new sentence; L6–L8 state no reader benefit. |
| H4 time/length estimate | not met (scope) | No "约 N 分钟 / 共 N 步" on the first screen; adding one is content. |
| L4 parallel list items | met | L14/L17 both imperative verb-initial; L15/L16 both "Confirm …". |
| L7 list items keep full meaning | met | All four items carry subject + verb and stand alone. |
| W2, W3, W5, W7, W8 | n/a | `rules.md`: the entire W group is inert under `scope=format`. |
| W9 negative → positive | n/a (exception anyway) | W group inert; note L12's negative phrasing sits in a warning, which W9 exempts. |
| A1 section-ending next step | n/a | Content axis; no H2 sections, and L17 is already an explicit action. |
| A2 per-step time estimate | not met (scope) | L14/L17 carry no estimates; adding them is content. |
| A3 default recommendation | n/a | No multi-option choice anywhere. |
| A5 "if you do one thing" | n/a | Content axis; 30-line document, not a long-doc first screen. |
| A6 decision-point criteria | n/a | No decision point ("only after approval" is a condition, not a fork). |
| **A7 expected output / verification** | **not met** | Neither step (L14, L17) shows what success looks like. The source states no output, exit state, or check to reuse, so this stays unmet by design — I did not invent output to close it. |
| **A8 one action per step** | **met** | L14 and L17 each hold one action; L15/L16 are separate confirmations. The approval clause on L17 is a branch, not a compound action. |
| **N7 progress marking (≥4 steps)** | **n/a** | The flow has 2 steps; the rule deliberately stays silent below 4. |
| C4 Chinese modifier order | n/a | CJK-only rule; document language is `en`. |

**Hint-only rules (no score effect):** S7 (>600 lines — n/a), L6 (>7 items — n/a), N3 (divider between H2s — no H2s), T5 (canonical warning label — the existing quote carries no 注意/警告 prefix, and adding one would be new wording), C6 (Chinese list punctuation — n/a).

### What I changed

**Nothing.** Every format-scope operation available against this document was tested against the case's constraints and rejected: there is no paragraph over the limits, no missing blank line, no missing fence language, no nesting to flatten, no heading level to fix, no TOC trigger (30 lines < 80), no token to reorder, and no optional branch worth folding. `fmt` independently reports the file as already canonical. Writing a "reformat" that only churns the file would have risked the boundary constructs this document exists to carry.

### What I deliberately did not change

- **The bold in `**Preview**`, `**first copy**`, `**second copy**` (L14, L30).** This is the sole deduction — `T2d`, bold density 8.3% vs the 8% cap, anchored at `output.md:1` because it is a document-level ratio over prose blocks; the contributing spans are L14 and L30. I verified the fix works and that the gate would *not* have stopped it: removing just the four `*` characters around `Preview` raises the script score to **100.0** and `verify` still returns pass. I declined anyway — this case requires preserving every original character, deleting the author's emphasis to satisfy a ratio is metric-gaming, and 8.3% is an artifact of a ~313-character prose body with 26 bold characters. `X5` (12% cap) is clear, so this is a T-axis deduction, not an anti-pattern.
- **The two `x ** 2`, `A->B` code spans, the `route /v2/items -> cache` block, the `?region=west#step-2` link target, `15 s` and `0`, and the YAML frontmatter** — all preserved verbatim; frontmatter is character-protected under `format`.
- **The repeated terms at L30.** Both copies stay ("retain the **first copy**. Retain the **second copy** too."). Repetition here is the fixture's point; nothing was deduplicated.
- **The warning text (L10–12).** Kept word-for-word, and it was not rewritten into new phrasing or moved to the top.
- **Information order.** Unchanged end to end — `S5`/`S6`-style block moves are off the table for this case.
- **No TL;DR, no emoji, no `<details>`, no new headings, no added time estimate or next-step line.** All of those are content operations, and the folding option would also have flipped `verify` to `unknown`.

### Target status: partial — stated as such

The anti-pattern requirement is met (X group = 0). The stronger target "no script deductions" is **not met**: one hit remains, `T2d` bold density 8.3% > 8% at `output.md:1`. It is clearable only by deleting original `*` characters, which this case forbids, so I kept the source text and am reporting the residual rather than editing around the metric.
