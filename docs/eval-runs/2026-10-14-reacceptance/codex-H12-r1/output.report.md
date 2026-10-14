Format-only review of `input.md` → `output.md`

Scope: `format`. Level: `deep` (`3`). Document type: boundary Markdown. Input was not overwritten.

Added two blank lines: after the Preview sentence and after its nested checks. These separate the parent action, its checks, and the approval-dependent Apply step. All original bytes remain in their original order. The source has 631 bytes; the output has 633 bytes. An exact reconstruction check confirmed that the only changes are two inserted LF bytes.

Deliberately unchanged: every original character, punctuation mark, Markdown marker, number, unit, condition, warning, link target, inline literal, code block, frontmatter field, and information order. The nested checks still belong to Preview. Apply still requires approval. The two copy reminders both remain. No headings, summary, checklist labels, estimates, explanations, or success results were added. The formatter preview proposed no changes.

Command results, using `.agents/skills/adhd-md/scripts/adhd_md.py`:

| Command arguments | Exit status | Result |
|---|---:|---|
| `audit input.md --level 3 --scope=format` | 0 | Script score 97.4 |
| `fmt input.md` | 0 | Preview only; no proposed changes |
| `audit output.md --level 3 --scope=format` | 0 | Script score 97.4 |
| `verify input.md output.md --scope=format` | 0 | `pass`; no hard failures, warnings, or unknowns |
| `report input.md output.md --scope=format --level 3` | 0 | No score changes |
| `report input.md output.md --scope=format --level 3 --json` | 0 | Saved as `output.validation.json` |

The audit exit status is a successful command execution, not a declaration that every readability rule passed. Verification covers the script's declared invariants; the additional exact reconstruction check establishes the narrower, stronger fact that this edit only inserts two newlines. No `unknown` was treated as a pass.

Script score: **97.4 → 97.4 (+0.0)**. This is not a final manually completed score; the script's band remains `null`.

| Dimension | Before | After | Delta |
|---|---:|---:|---:|
| First-screen orientation | 100.0 | 100.0 | 0.0 |
| Chunking | 100.0 | 100.0 | 0.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Typography consistency | 80.0 | 80.0 | 0.0 |
| Naturalness | 100.0 | 100.0 | 0.0 |

Anti-pattern deductions: **0 → 0**; script X-group hits: none. M-group findings: **0 → 0**.

Remaining script finding: **T2d**, reported at `output.md:1`, bold density **8.3%**, above the **8%** threshold. The original emphasis is retained because removing its markers would violate the character-preservation constraint. No filler or spacing was added to manipulate the score. This finding does not trigger X5, whose threshold is greater than 12%. Full readability compliance is not claimed.

Coverage for deep/format: 41 rules; 23 script-checked, 5 advisory-only, 10 requiring judgment, 2 formatter-only, and 1 verification gate. The score includes all applicable axes even though findings and coverage are filtered to format.

The script leaves **32 rules unjudged/unscored across all axes**: S4, S5, S6, S8, H3, H4, P2, P5, L2, L4, L7, W2, W3, W5, W7, W8, W9, A1, A2, A3, A5, A6, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8. The 10 within format coverage are S5, S6, P2, P5, L2, N4, T3, X6, X7, X8. The following manual assessments are separate from the script score. “Not applicable” and out-of-scope rules are not machine passes. Locations refer to the final `output.md`.

| Rule | Manual assessment | Location and reason |
|---|---|---|
| S4 | Not satisfied; content axis | Line 6 is a topic title. Rewording it is outside format scope and the preservation constraint. |
| S5 | Not applicable | Lines 6–32 contain no conclusion block to move. Original information order must also remain fixed. |
| S6 | Not applicable | Lines 1–32 are the declared boundary Markdown sample, not a document requiring one of the optional type skeletons. Reordering is forbidden. |
| S8 | Not applicable | Line 6 is the sole heading; there are no separate chapters requiring opening purpose statements. |
| H3 | Not satisfied; content axis | Lines 6–15 contain no reader-outcome statement. Adding one would add content. |
| H4 | Not satisfied; content axis | Lines 6–15 contain no reading-time or length estimate. The timeout at line 23 is a parameter, not a reading estimate. |
| P2 | Satisfied | Paragraphs at lines 8, 30, and 32 each address one subject. |
| P5 | Not applicable | The quotation at lines 10–12 is only three lines, below the greater-than-five-line threshold. |
| L2 | Satisfied | Lines 14–19 already enumerate actions and checks; the short prose at lines 8 and 32 needs no forced list conversion. |
| L4 | Satisfied; content axis | Lines 14–19 use imperative actions, with parallel Confirm checks. |
| L7 | Satisfied; content axis | Each item at lines 14–19 retains its full imperative and object; Apply retains its approval condition. |
| W2 | Satisfied; content axis | Lines 8–32 use active imperatives and copular descriptions, with no passive construction requiring revision. |
| W3 | Not applicable | Lines 8–32 contain no long parenthetical prose aside. Link syntax is not a parenthetical aside. |
| W5 | Not applicable | No unexplained acronym is introduced. Line 8 explicitly identifies the two literal examples. |
| W7 | Satisfied; content axis | Lines 10–19, 30, and 32 use direct, present imperative verbs with an understood reader as subject. |
| W8 | Satisfied; content axis | Lines 8–32 contain no three-level nested clause. The approval condition at line 19 remains attached to Apply. |
| W9 | Satisfied; content axis | The negative instruction at line 12 is a warning, an explicit exception to positive phrasing. |
| A1 | Satisfied; content axis | The action sequence ends with the explicit Apply action and approval prerequisite at line 19; line 30 also names the rollback reference. |
| A2 | Not satisfied; content axis | Steps at lines 14–19 lack duration estimates. The timeout at line 23 cannot substitute for a task estimate. |
| A3 | Not applicable | Lines 14–19 offer no competing options requiring a default recommendation. |
| A5 | Not applicable | This is a short 32-line sample, not a long document needing a single-priority entry point. |
| A6 | Satisfied; content axis | Line 19 explicitly gates Apply on approval; lines 16–17 retain the two preview checks. |
| A7 | Not satisfied; content axis and source gap | Lines 16–17 provide preview checks, but Apply at line 19 has no expected result or success verification. None can be invented from this source. |
| A8 | Not satisfied under a conservative top-level-step reading | Preview at line 14 groups the two confirmation actions at lines 16–17. Each leaf item is single-action, but the parent remains compound. Renumbering or rewriting would violate the preservation constraint. |
| N4 | Not applicable | Lines 1–32 contain no long optional branch needing folding. |
| N7 | Not applicable | Lines 14 and 19 are two top-level workflow steps. The two subordinate checks do not make this a four-step top-level process. |
| T3 | Satisfied | Lines 8, 16–17, and 23–24 use code for literals; lines 14 and 32 use bold for the existing salient action/copy phrases. The literal `x ** 2` remains intact. |
| C4 | Not applicable | The document is English, as confirmed by audit. |
| X3 | Satisfied; no deduction | Lines 14–19 retain complete list-item meanings rather than isolated keywords. |
| X6 | Satisfied; no deduction | The table at lines 21–24 contains short comparable field/value entries, not narrative prose. |
| X7 | Satisfied; no deduction | Lines 1–32 contain no folded content; the full main path stays visible. |
| X8 | Satisfied; no deduction | Lines 1–32 contain no repeated boilerplate section templates or filler sections. |

Additional X-group checks:

| Rule | Assessment | Evidence |
|---|---|---|
| X1 | Satisfied; no deduction | No emoji anywhere in the output. |
| X2 | Satisfied; no deduction | One H1 at line 6; no added headings or fragmented sections. |
| X4 | Satisfied for this edit | Verification passed, and exact reconstruction confirms two inserted LF bytes with no original bytes removed, changed, or reordered. |
| X5 | Satisfied; no deduction | Script-reported bold density of 8.3% is below the greater-than-12% anti-pattern threshold. T2d remains separately unsatisfied. |

All 32 returned judgment rules have an explicit manual disposition above; they remain unscored by the script. This report does not turn missing estimates, missing success criteria, the compound parent step, or the remaining T2d finding into passes.
