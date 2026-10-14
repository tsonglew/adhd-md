**Created [output.md](output.md) with `scope=format`, `level=deep` (`--level 3`).** The input was not overwritten. Only two blank lines were inserted: before the nested preview checks and before step 2. All original bytes remain in their original order.

**Checks and exit statuses**

| Command | Exit status | Result |
|---|---:|---|
| `audit input.md --level 3 --scope=format` | 0 | Script score 97.4; one T2d finding |
| `fmt input.md` (preview only) | 0 | No automatic changes proposed |
| `audit output.md --level 3 --scope=format` | 0 | Script score 97.4; same T2d finding |
| `verify input.md output.md --scope=format` | 0 | `pass`; no hard failures, warnings, or unknowns |
| `report input.md output.md --level 3 --scope=format` | 0 | Anti-pattern deductions 0; verification passed |
| Additional byte-preservation check | 0 | Exactly two inserted LF blank lines; input hash unchanged |

The audit, verify, and report commands also ran with `--json`; each JSON invocation exited 0. Commands used `.agents/skills/adhd-md/scripts/adhd_md.py` with Python 3. Raw results and exit records are in [checks](checks/), including [verification](checks/verify.json), [before/after report](checks/report.json), [preservation evidence](checks/preservation.json), and the [complete diff](checks/changes.diff).

**Script score: 97.4 → 97.4 (delta 0.0).** This is not a complete manually scored rating. The script leaves judgment rules unscored and sets `score.band` to `null`.

| Dimension | Before | After | Delta |
|---|---:|---:|---:|
| Opening / conclusion | 100.0 | 100.0 | 0.0 |
| Chunking | 100.0 | 100.0 | 0.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Formatting consistency | 80.0 | 80.0 | 0.0 |
| Naturalness | 100.0 | 100.0 | 0.0 |

**Remaining finding:** T2d reports 8.3% bold density against an 8% limit (reported at line 1 in each file). The original emphasis markers were preserved under the character-preservation requirement. Full rule compliance is not claimed. X-group anti-pattern deductions remain **0 → 0**, with no script X hits; M-group hits remain **0 → 0**.

**Deliberately unchanged:** the frontmatter, title, punctuation, all emphasis and inline code, warning block, three-space bullet indentation, numbering, approval prerequisite, table values and units, complete fenced code block, full link target, and both repeated-copy statements. No headings, summary, time estimates, checkbox markers, success criteria, or reordered blocks were introduced. The existing small document did not need a new skeleton; deep-level review remained bounded by the preservation requirements.

**Unjudged by the script; manually reviewed below**

The audit lists 32 judgment rules across all scoring axes. Of these, 10 are in the format-scope coverage: S5, S6, P2, P5, L2, N4, T3, X6, X7, X8. The table records all 32, including content rules for which edits are outside scope. These judgments do not change the reported script score. No unjudged rule is treated as an automatic pass, and no `unknown` is reported as a pass.

Evidence uses original `input.md` line numbers. Input lines 1–14 retain their output numbers; lines 15–16 move by +1; lines 17–30 move by +2.

| Rule | Judgment | Evidence and reason |
|---|---|---|
| S4 | Not met; content scope excluded | Line 6 is a topic title, not a conclusion. Its wording must remain unchanged. |
| S5 | Not applicable | Lines 8–30 contain examples and instructions, with no existing conclusion block to move; ordering is fixed. |
| S6 | Not applicable | Lines 1–30 are a short boundary Markdown fixture, with no applicable tutorial/report skeleton to impose. Ordering is fixed. |
| S8 | Not met; content scope excluded | Line 8 identifies literal examples but does not state a section purpose. No new purpose statement may be added. |
| H3 | Not met; content scope excluded | Lines 6–14 contain no explicit reader-benefit statement. |
| H4 | Not met; scope limited | Lines 6–14 contain no reading-time or length estimate. Adding one would add content. |
| P2 | Met | Line 8 discusses literal notation; line 28 links rollback notes; line 30 discusses retaining repeated copies. Each paragraph has one topic. |
| P5 | Not applicable | Lines 10–12 form a three-line quote, below the greater-than-five-line threshold. |
| L2 | Not met; retained | Line 30 contains two parallel retention instructions in prose. The original characters and compact paragraph were retained. |
| L4 | Met; content scope excluded | Lines 14–17 use parallel imperative verbs: Preview, Confirm, Confirm, Apply. |
| L7 | Met; content scope excluded | Lines 14–17 retain complete instructions, their objects, and the approval prerequisite. |
| W2 | Met; content scope excluded | Lines 8–30 use active imperatives or copular descriptions; no passive construction needs correction. |
| W3 | Not applicable | Lines 8–30 have no parenthetical prose insertion. The link destination is Markdown syntax. |
| W5 | Not applicable | Line 8 contextualizes the two literal examples; there is no unexplained prose acronym requiring expansion. |
| W7 | Met; content scope excluded | Lines 10–17 use direct present-tense imperatives with an understood second-person subject. |
| W8 | Met; content scope excluded | Line 8 has coordinated descriptions; lines 10–30 contain no deeply nested clauses. |
| W9 | Met; content scope excluded | The negative instruction at line 12 is a warning, which the rule explicitly exempts. |
| A1 | Not met; content scope excluded | Lines 17–30 do not provide an explicit follow-up action after applying the plan; the rollback link is a reference. |
| A2 | Not met; content scope excluded | Lines 14–17 have no per-step time estimates. The `15 s` timeout at line 21 is a field value, not an execution-time estimate. |
| A3 | Not applicable | Lines 14–22 offer no alternative options requiring a default recommendation. |
| A5 | Not applicable | The 30-line source is short; the rule targets a single-action entry point for long documents. |
| A6 | Met; content scope excluded | Lines 15–17 supply the existing checks and the explicit prerequisite “only after approval.” No additional decision criteria are inferred. |
| A7 | Not met; source gap | Lines 15–16 give preview checks. Line 17 provides no expected result or success test for applying the plan. Approval is a prerequisite, not a success result. |
| A8 | Not met at numbered-step level | Lines 14–16 group preview and two confirmations under step 1. Each leaf instruction is single-action, but the numbered step remains compound. Nesting and numbering are preserved. |
| N4 | Not applicable | Lines 8–30 have no lengthy optional branch needing a fold. |
| N7 | Not applicable | Lines 14–17 contain two main steps with subordinate checks, not four sequential top-level steps. |
| T3 | Met | Lines 8, 15–16, 21–22 use code for literals; lines 14 and 30 use bold for action/copy emphasis. The stars inside `x ** 2` remain literal. |
| C4 | Not applicable | Lines 1–30 are English, with no Chinese long modifier construction. |
| X3 | Met; no hit | Lines 14–17 retain full imperative clauses rather than isolated keywords. |
| X6 | Met; no hit | Lines 19–22 contain a compact field/value table, not narrative prose forced into cells. |
| X7 | Met; no hit | Lines 1–30 contain no folded main-path content. |
| X8 | Met; no hit | Line 6 is the only heading; there are no repeated template subheadings or filler sections. |

All 32 script-unjudged rules have an explicit manual disposition above; none remains manually unjudged. Several are unmet or inapplicable, so this is not a claim that every rule passed.

**Complete anti-pattern review**

| Rule | Result | Evidence |
|---|---|---|
| X1 | No hit | No emoji in either file; audit has no X1 finding. |
| X2 | No hit | One H1 and no fragmented subsections; audit has no X2 finding. |
| X3 | No hit | Complete instructions retained at input lines 14–17. |
| X4 | Preservation check passed | Final verify returns `pass`; byte comparison proves the only changes are two inserted blank lines. |
| X5 | No hit | Script density is 8.3%, below the X5 12% threshold. The stricter T2d 8% finding remains. |
| X6 | No hit | Existing two-column field/value table retained. |
| X7 | No hit | No folds were added. |
| X8 | No hit | No template sections were added. |

Format/deep coverage is 41 rules: 23 script-checked, 5 hint-only, 10 requiring judgment, 2 automatic-format rules, and 1 hard gate. Hint-only rules are S7, L6, N3, T5, C6. S7/L6 thresholds are not reached; there are no H2 boundaries for N3; adding a T5 warning label would add content; C6 concerns Chinese list punctuation and is inapplicable here. The verifier checks its declared Markdown subset; the separate byte check establishes the stricter character/order preservation for this particular edit.
