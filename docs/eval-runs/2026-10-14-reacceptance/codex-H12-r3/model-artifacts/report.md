# H12 formatting report

Used `scope=format`, `level=deep` (`--level 3`), and the skill snapshot at `.agents/skills/adhd-md/SKILL.md`.

Created `output.md` as an exact, 631-byte copy of `input.md`. The input was not overwritten. No document characters, markup, whitespace, content, or ordering changed. The formatter's preview reported that formatting was already normalized. The remaining bold-density finding cannot be removed while preserving every original character; no formatting changes were made solely to increase the score.

**Command results**

Commands below use `.agents/skills/adhd-md/scripts/adhd_md.py`.

| Command arguments | Exit status | Result |
|---|---:|---|
| `audit input.md --level 3 --scope=format` | 0 | Script score 97.4; T2d finding |
| `fmt input.md` | 0 | Preview only; no changes needed |
| `audit output.md --level 3 --scope=format` | 0 | Script score 97.4; T2d finding |
| `verify input.md output.md --scope=format` | 0 | `pass` |
| `report input.md output.md --scope=format --level=3` | 0 | Unchanged scores; verification passed |
| `report input.md output.md --scope=format --level=3 --json` | 0 | `status: pass`, `identical: true`, no hard failures, warnings, or unknowns |

An independent byte comparison also passed, and the input's SHA-256 still matches its pre-copy value. Both files have SHA-256 `ed563572dd10b7cff97f699ed209cd8b2d80c09fc4ad863a8cb81df56cc315a8`.

`pass` here is the actual verifier status, not a relabeling of `unknown`. Byte identity additionally establishes exact preservation for this output; it does not establish compliance with every readability rule.

**Script score: 97.4 → 97.4 (delta 0.0)**

| Dimension | Before | After | Delta |
|---|---:|---:|---:|
| First-screen clarity | 100.0 | 100.0 | 0.0 |
| Chunking | 100.0 | 100.0 | 0.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Typography consistency | 80.0 | 80.0 | 0.0 |
| Naturalness | 100.0 | 100.0 | 0.0 |

Anti-pattern deductions: **0 → 0**, with no script X-group hits. M-group findings: **0 → 0**. The sole reported finding is **T2d**, measured bold density **8.3%**, above the **8%** limit. The script attaches this document-wide finding to line 1; the existing bold spans occur on lines 14 and 30. It is distinct from X5's greater-than-12% threshold. Full readability compliance is **not met**.

**Unjudged rules and coverage**

The script leaves these 32 rules unjudged/unscored: S4, S5, S6, S8, H3, H4, P2, P5, L2, L4, L7, W2, W3, W5, W7, W8, W9, A1, A2, A3, A5, A6, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8. They are not machine passes. The following manual judgments do not modify the script score or turn it into a complete score.

Format/deep coverage reports 41 applicable rules: 23 script-checked, 5 advisory, 10 judgment-only, 2 formatter-only, and 1 verification gate. The 10 format-scope judgment rules are S5, S6, P2, P5, L2, N4, T3, X6, X7, X8. The script score and its 32-rule unjudged list cover all axes, despite scope-filtered findings and coverage.

All line references below apply equally to `input.md` and `output.md`. Content-axis observations are recorded for transparency; they do not authorize rewriting.

| Rule | Manual status | Location and reason |
|---|---|---|
| S4 | Not met | L6: topic heading, not a conclusion. Wording is protected by format scope. |
| S5 | Not applicable | L6–30: no conclusion block exists to move; original order is required. |
| S6 | Not applicable | L1–30: supplied type is boundary Markdown, not one of the skill's six document templates. No template imposed. |
| S8 | Not met | L6–8: opening defines literals rather than stating what the section helps solve. Adding that statement exceeds scope. |
| H3 | Not met | L6–15: no explicit reader-benefit statement. Adding one exceeds scope. |
| H4 | Not met | L1–15: no reading-time or document-length estimate. Adding one exceeds scope. |
| P2 | Met | L8, L28, L30: each prose paragraph has a single subject. |
| P5 | Not applicable | L10–12: quotation has three source lines, below the greater-than-five-line threshold. |
| L2 | Met | L15–16: parallel checks already have separate list items. L30 is a short, coherent two-sentence paragraph. |
| L4 | Met | L14–17: imperative actions; both parallel child items begin with Confirm. |
| L7 | Met | L14–17: list items retain complete imperative clauses, including objects and the approval condition. |
| W2 | Met | L8–30: prose and instructions use active constructions. |
| W3 | Not applicable | L8–30: no parenthetical insertion needs splitting. |
| W5 | Not applicable | L8–30: literals are identified as such; no unexplained prose acronym requires expansion. |
| W7 | Met | L10–17 and L30: instructions use present imperatives with an implied reader as subject. |
| W8 | Met | L8–30: no deeply nested subordinate clauses. |
| W9 | Met | L12: negative wording is a warning, explicitly allowed by the rule; preserved verbatim. |
| A1 | Not met | L17–30: no explicit next-action statement at the end. Adding one exceeds scope. |
| A2 | Not met | L14–17: no step-duration estimates. L21's timeout is not a duration estimate for a step. |
| A3 | Not applicable | L14–22: no alternatives requiring a default recommendation. |
| A5 | Not applicable | L1–30: short sample, not a long document needing a single-action entry point. |
| A6 | Met | L17: approval is the explicit condition before applying the plan; L15–16 provide preview checks. |
| A7 | Not met | L15–16 provide preview checks, but L17 gives no Apply success result or verification. Approval is a precondition. Missing results cannot be invented. |
| A8 | Met | L14–17: each explicitly separated list item contains one imperative action. Two child checks stay under Preview; Apply retains its approval condition. |
| N4 | Not applicable | L1–30: no lengthy optional branch requires folding. |
| N7 | Not applicable | L14–17: two top-level steps, below the four-step threshold. Child checks remain subordinate. |
| T3 | Met | L8, L14–16, L21–22, L30: code marks literal values; existing bold marks the key action and distinct copies. Density is separately flagged by T2d. |
| C4 | Not applicable | L1–30: English document; no Chinese attributive construction. |
| X3 | Met | L14–17: complete imperative sentences, not keyword fragments. |
| X6 | Met | L19–22: compact two-column table holds comparable field/value data. |
| X7 | Met | L1–30: no content hidden in folds. |
| X8 | Met | L6–30: one H1; no repeated empty template sections. |

No manual judgment is left as `unknown`; the unmet rules above remain unmet. This does not change the script's unscored-rule list.

**Complete anti-pattern review**

Here, Met means the prohibition is respected.

| Rule | Status | Evidence |
|---|---|---|
| X1 | Met | L1–30: no emoji. |
| X2 | Met | L6: single H1; no fragmented sections. |
| X3 | Met | L14–17: complete imperative clauses. |
| X4 | Met | Verifier passed; complete files are byte-identical. |
| X5 | Met | Script reports 8.3% bold, below X5's 12% boundary; T2d remains unmet. |
| X6 | Met | L19–22: appropriate field/value table. |
| X7 | Met | L1–30: no folds hiding the main path. |
| X8 | Met | L6–30: no repeated template filler. |

**What changed and what was deliberately preserved**

Only a separate output file and this report were created. No document edits were made. Preserved exactly: YAML metadata (L1–4), title (L6), both inline literals including literal asterisks (L8), both warnings (L10–12), list numbering and nested check ownership (L14–17), approval precondition (L17), table values and units (L19–22), entire fence including label and body (L24–26), rollback link including query and fragment (L28), and both repeated-term sentences in their original order (L30). No commands from the document were executed.

The existing bold markup remains because removing it would violate character preservation. No summary, estimate, success output, heading, checklist, fold, or reordered block was added. The deep level was used for audit and review; it did not override the user's preservation constraints.
