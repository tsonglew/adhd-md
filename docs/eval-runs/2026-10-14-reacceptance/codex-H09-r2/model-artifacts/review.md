# Formatting review

Scope: `format`. Level: `deep` (`3`). Language: English. Document type: reference.
Output: `output.md`. The original `input.md` was not overwritten.

## Commands and exit status

All commands use `.agents/skills/adhd-md/scripts/adhd_md.py`.

| Command arguments | Exit status | Result |
|---|---:|---|
| `audit input.md --level 3 --scope=format` | 0 | Script score 100.0; no findings |
| `fmt input.md` | 0 | Preview only; no automatic changes needed |
| `audit output.md --level 3 --scope=format` | 0 | Script score 100.0; no findings |
| `verify input.md output.md --scope=format` | 0 | `pass`; no hard failures, warnings, or unknowns |
| `report input.md output.md --scope=format --level=3` | 0 | Score and deductions unchanged; verification passes |
| `report input.md output.md --scope=format --level=3 --json` | 0 | Saved as `validation.json` |

The script score is **100.0 → 100.0 (delta 0.0)**. It is not a complete judgment score. The script leaves 32 rules unjudged across all axes; 10 are within the format coverage. Each is reviewed below. No `unknown` result has been treated as a pass. There are no unresolved manual judgments in this review, but several content requirements are unmet and were preserved under the format-only constraint.

| Dimension | Before | After | Delta |
|---|---:|---:|---:|
| First-screen usefulness | 100.0 | 100.0 | 0.0 |
| Chunking | 100.0 | 100.0 | 0.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Formatting consistency | 100.0 | 100.0 | 0.0 |
| Naturalness | 100.0 | 100.0 | 0.0 |

Anti-pattern deductions: **0 → 0**; script X hits: none. Manual X review also found no violations. M-group findings remain zero.

Format coverage: 41 applicable rules; 23 script-checked, 5 advisory, 10 judgment-only, 2 automatic-format rules, and 1 preservation gate. Coverage is not a claim that every rule passed.

## Changes and deliberate limits

The two prose paragraphs became two short groups of full-sentence reference notes. Added emphasis marks the retry exception and restart condition. Only Markdown list/emphasis markers and line breaks were inserted; no source characters were deleted, substituted, or reordered. The original spaces at sentence boundaries now serve as the spaces after list markers.

The title, four-column reference table, YAML fence and body, punctuation, numerical values and ranges, units, and information order remain intact. No headings, summary, checklist, time estimate, instructions, links, or technical claims were added. The short reference already begins with its lookup table; deep-level review did not justify changing that structure. There are no source link targets to alter.

An insertion-only character-sequence check passed. Reversing the exact formatting additions restored the input byte for byte. The input was checked again after writing and was unchanged. Input SHA-256: `6374a44faee4d2ec26c2305e45130548a8730bb7adefbb0a4e110372097ca71e`.

| Preserved information | Output location |
|---|---|
| `visibilitySeconds`: default 45; range 5–600; visibility of unacknowledged jobs | Line 5 |
| `maxAttempts`: default 3; range 1–8; includes first delivery attempt | Line 6 |
| `backoffMs`: default 400; range 100–5000; base retry delay | Line 7 |
| `deadLetterAfter`: default 8; range 1–20; failed jobs moved to dead-letter queue | Line 8 |
| Initial delivery counts; value `1` disables retries | Lines 10–11 |
| Authentication errors `401` and `403` are never retried, even when `maxAttempts` is greater than one | Line 12 |
| Complete original YAML example: `queue`, `maxAttempts: 4`, `backoffMs: 800` | Lines 14–18 |
| Configuration changes take effect after worker restart | Line 20 |
| `visibilitySeconds` uses seconds; `backoffMs` uses milliseconds | Line 21 |

## All rules left unjudged by the script

These are manual assessments, not additions to the numeric script score. “Not applicable” is distinct from “met.” Content-axis observations do not authorize wording changes.

| Rule | Manual status | Evidence and reason |
|---|---|---|
| S4 | Unmet; content scope required | Line 1 remains the topic title “Queue configuration”; changing it to a conclusion would change wording. |
| S5 | Met | Lines 3–8 put the reference answer table first. No block movement is necessary. |
| S6 | Met | Lines 1–21 retain the reference structure: lookup table, behavioral notes, minimal example, activation and units. |
| S8 | Unmet; content scope required | Lines 1–3 have no introductory purpose sentence. Adding one is prohibited. |
| H3 | Unmet; content scope required | Lines 1–15 contain no explicit reader-outcome statement. No new statement was invented. |
| H4 | Unmet; content scope required | Lines 1–15 contain no reading-time or length estimate. This also applies to reference documents, but adding an estimate would violate the user's constraint. |
| P2 | Met | Lines 10–12 and 20–21 each contain one focused note; the final note compares units as one topic. |
| P5 | Not applicable | Lines 1–21 contain no quotation blocks. |
| L2 | Met | Lines 10–12 and 20–21 present the existing reference statements as bullets in their original order. |
| L4 | Met | Lines 10–12 and 20–21 consistently use declarative sentences with explicit subjects and present-tense predicates. |
| L7 | Met | All five bullets retain complete sentences; line 11 retains its original contextual connection to `maxAttempts` in line 10. |
| W2 | Unmet; content scope required | Lines 12 and 21 retain passive constructions “are never retried” and “is measured”; these exceed the rule's 10% threshold. |
| W3 | Not applicable | The parenthetical error codes in line 12 do not exceed the five-word threshold. |
| W5 | Unmet; content scope required | Line 8 uses “dead-letter queue” without defining the domain term. Adding an explanation is prohibited. |
| W7 | Not applicable | Lines 3–21 are descriptive reference data, not direct instructions requiring second-person address. |
| W8 | Met | Lines 10–12 and 20–21 have no deeply nested subordinate clauses. The exception and restart condition remain attached to their original statements. |
| W9 | Met | Line 12's negative assertion is an essential retry exception, which the rule explicitly allows preserving. |
| A1 | Not applicable | Lines 14–18 provide a configuration example; the document contains no executable procedure requiring a next-step instruction. |
| A2 | Not applicable | Lines 1–21 contain no timed operational steps. |
| A3 | Not applicable | Lines 3–8 list factual defaults and valid ranges, not competing recommended approaches. No recommendation or rationale was invented. |
| A5 | Not applicable | This is a short reference, not a long document requiring a single-action entry point. |
| A6 | Not applicable | Lines 3–21 describe parameter behavior rather than a branching decision procedure. |
| A7 | Not applicable | Lines 14–18 are a YAML specimen, not executable steps. The source supplies no success output or validation procedure; none was added or claimed. |
| A8 | Not applicable | Lines 10–12 and 20–21 are reference notes, not action steps. The two unit definitions in line 21 are facts, not a compound instruction. |
| N4 | Not applicable | Lines 1–21 contain no long optional branch. The table and example remain visible for lookup. |
| N7 | Not applicable | No procedure with four or more steps exists. The four table rows are settings, not steps. |
| T3 | Met | Lines 3–21 consistently use code style for literal setting names/values and two bold spans for critical constraints. |
| C4 | Not applicable | The document is English; the Chinese modifier rule does not apply. |
| X3 | Met; no violation | Lines 10–12 and 20–21 preserve complete original sentences instead of reducing them to keywords. |
| X6 | Met; no violation | Lines 3–8 compare four settings using consistent fields. No narrative was forced into a new table. |
| X7 | Met; no violation | No content is collapsed or hidden. |
| X8 | Met; no violation | The only heading is the original title; no repeated template sections or filler were added. |

## Remaining X-group checks

| Rule | Result | Evidence |
|---|---|---|
| X1 | No violation | No emoji present or added. |
| X2 | No violation | One heading across 21 lines; no small artificial sections. |
| X4 | Preservation checks pass | `verify` exits 0 with no unknowns; insertion-only and exact-reversal checks also pass. This is not a general semantic-equivalence guarantee. |
| X5 | No violation | Two short bold spans; the audit finds neither excess emphasis nor an X5 deduction. |

The five advisory rules were also reviewed: S7 does not apply to a 21-line file; L6 does not apply to lists of three and two items; N3 has no H2 sections to separate; T5 would require a new warning label, so the original retry exception is emphasized without adding words; C6 is a Chinese punctuation rule and does not apply.
