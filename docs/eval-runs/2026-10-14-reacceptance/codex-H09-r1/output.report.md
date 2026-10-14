# Formatting review

Scope: `format`. Level: `deep` (`3`). Language: English. Document type: reference.

Created `output.md`; `input.md` was not overwritten. Used the case snapshot at `.agents/skills/adhd-md/SKILL.md`.

**Changed:** converted the two prose paragraphs into groups of three and two complete-sentence bullets. Added emphasis to “never retried” and “after the worker restarts”. All changes are formatting insertions.

**Intentionally unchanged:** every original character, punctuation mark, number, unit, condition, exception, and information order; the heading, parameter table, inline code, and complete YAML block. The reference table remains first. No summary, reading estimate, new headings, checklist, folding, recommendations, or validation behavior was added. The deep setting does not override the user's stricter preservation constraints.

| Command, using `.agents/skills/adhd-md/scripts/adhd_md.py` | Exit status | Result |
|---|---:|---|
| `audit input.md --level 3 --scope=format` | 0 | Script score 100.0; no findings |
| `fmt input.md` (preview only) | 0 | No deterministic formatting changes suggested |
| `audit output.md --level 3 --scope=format` | 0 | Script score 100.0; no findings |
| `verify input.md output.md --scope=format` | 0 | `pass` |
| `report input.md output.md --scope=format --level=3` | 0 | Script score 100.0 → 100.0; verification passes |
| `report input.md output.md --scope=format --level=3 --json` | 0 | `status=pass`, `ok=true`; no hard failures, warnings, or unknowns |

These are script scores, not a complete quality score or proof of semantic equivalence. The script leaves judge rules unscored; the manual review below does not change its numeric score. No `unknown` result was treated as a pass.

| Script dimension | Before | After | Delta |
|---|---:|---:|---:|
| First-screen clarity | 100.0 | 100.0 | 0.0 |
| Chunking | 100.0 | 100.0 | 0.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Typography consistency | 100.0 | 100.0 | 0.0 |
| Naturalness | 100.0 | 100.0 | 0.0 |
| Total | 100.0 | 100.0 | 0.0 |

Script anti-pattern deductions: **0 → 0**; `x_hits={}` before and after. M-group findings: **0 → 0**. Manual X-group review also found no anti-pattern deductions. The document is not claimed to meet every skill rule: H4 remains unmet, along with the other content limitations recorded below.

Preservation was also checked beyond the format verifier: reversing only the inserted formatting reconstructs the input byte for byte, and all original bytes remain in the output in their original order. An independent reviewer confirmed there are no byte deletion or replacement operations. The original input SHA-256 remained `6374a44faee4d2ec26c2305e45130548a8730bb7adefbb0a4e110372097ca71e`.

| Preserved source information | Input location | Output location |
|---|---|---|
| Heading; table headers, alignment markers, and row order | `input.md:1–8` | `output.md:1–8` |
| `visibilitySeconds`: default 45, range 5–600; visibility of an unacknowledged job | `input.md:5` | `output.md:5` |
| `maxAttempts`: default 3, range 1–8; first delivery included | `input.md:6` | `output.md:6` |
| `backoffMs`: default 400, range 100–5000; base retry delay | `input.md:7` | `output.md:7` |
| `deadLetterAfter`: default 8, range 1–20; failed jobs moved to dead-letter queue | `input.md:8` | `output.md:8` |
| Initial delivery counts; value `1` disables retries | `input.md:10` | `output.md:10–11` |
| Authentication errors `401` and `403` are never retried, even when `maxAttempts` is greater than one | `input.md:10` | `output.md:12` |
| Complete YAML example, including language tag, indentation, `maxAttempts: 4` and `backoffMs: 800` | `input.md:12–16` | `output.md:14–18` |
| Changes take effect after worker restart | `input.md:18` | `output.md:20` |
| `visibilitySeconds` uses seconds; `backoffMs` uses milliseconds | `input.md:18` | `output.md:21` |

There are no link targets in the input or output. No product claims were independently fact-checked; this task preserves the supplied reference.

The audit reports **32 rules unjudged/unscored by the script**, across all axes:

`S4, S5, S6, S8, H3, H4, P2, P5, L2, L4, L7, W2, W3, W5, W7, W8, W9, A1, A2, A3, A5, A6, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8`.

Within `format` coverage, the 10 judge rules are `S5, S6, P2, P5, L2, N4, T3, X6, X7, X8`. Coverage is 41 rules: 23 script checks, 5 hints, 10 judge rules, 2 automatic-format rules, and 1 verification gate. Scope filters displayed findings and coverage; the script score still includes all applicable axes. No findings does not mean all rules passed.

Every audit-listed judge rule is assessed below. “Not applicable” is distinct from “satisfied”. Content-rule observations describe retained source limitations; they do not authorize wording changes. All locations refer to `output.md`.

| Rule | Manual status | Location and reason |
|---|---|---|
| S4 | Not satisfied; format constraint | Line 1: original topic heading is retained; changing it to a conclusion would change wording. |
| S5 | Satisfied | Lines 3–8: the lookup answers already appear first; no block movement is needed. |
| S6 | Satisfied | Lines 3–21: parameter table first, then behavior notes, example, and timing/units; appropriate reference structure. |
| S8 | Not satisfied; format constraint | Lines 1–3: no opening explanatory sentence before the table; adding one would add content. |
| H3 | Not satisfied; format constraint | Lines 1–8: no explicit reader-benefit sentence; adding one is prohibited. |
| H4 | Not satisfied; format constraint | Lines 1–15: no reading-time or length estimate. Reference documents are not exempt, but the source supplies none and the user prohibits additions. |
| P2 | Satisfied | Lines 10–12 and 20–21: each bullet treats one subject; both units remain together as one unit-convention note. |
| P5 | Not applicable | Lines 1–21: no quotation blocks. |
| L2 | Satisfied | Lines 10–12 and 20–21: independent reference facts are now bullets using the original sentences. |
| L4 | Satisfied | Lines 10–12 and 20–21: bullets consistently use declarative statements with subjects and present-tense predicates. |
| L7 | Satisfied | Lines 10–12 and 20–21: complete statements retain their subjects, predicates, conditions, and punctuation. |
| W2 | Not satisfied; format constraint | Lines 12 and 21 retain passive constructions, including “are never retried” and both “is measured” clauses. Their proportion exceeds the rule's 10% target; rewriting is prohibited. |
| W3 | Satisfied | Line 12: the parenthetical consists only of `401` and `403`, below the long-parenthesis threshold. |
| W5 | Not applicable | Lines 3–21: no prose acronym requires a first-use expansion; parameter names have behavior descriptions in the table. |
| W7 | Not applicable | Lines 3–21: this is a parameter reference, not instructions addressing a reader; second-person rewriting is outside scope. |
| W8 | Satisfied | Lines 10–12 and 20–21: no three-level nested subordinate clauses; the exception remains a single complete statement. |
| W9 | Satisfied | Line 12: “never retried” expresses a necessary exception, which the rule permits to remain negative. |
| A1 | Not satisfied under the code-block heuristic; format constraint | Lines 14–20: the rubric treats a section containing code as executable, but the YAML example has no explicit imperative next step. The restart sentence states behavior; no instruction was invented. |
| A2 | Not applicable | Lines 14–20: no timed executable steps; YAML configuration is an example. |
| A3 | Not applicable | Lines 3–8: defaults are documented, but there is no choice among competing approaches needing a recommendation and rationale. |
| A5 | Not applicable | Lines 1–21: this is a short reference, not a long document needing a single-action entry point. |
| A6 | Not applicable | Lines 3–21: no procedural decision point; existing setting behavior and exceptions remain available for lookup. |
| A7 | Not applicable to a step sequence; source gap retained | Lines 14–20: the YAML sample is not a command or executable step. No success output or verification method is supplied. If used as an implementation procedure, that validation would be missing; none was invented. |
| A8 | Not applicable | Lines 10–12 and 20–21: bullets are facts, not action steps. The example's two settings do not constitute a compound instruction. |
| N4 | Not applicable | Lines 1–21: the short reference has no separate optional/deep branch; its lookup table stays visible. |
| N7 | Not applicable | Lines 1–21: no process of four or more steps. Five factual bullets do not become a procedure. |
| T3 | Satisfied | Lines 5–21: code style continues to identify literal settings/values; two bold phrases identify the key behavioral constraints. |
| C4 | Not applicable | Lines 1–21: English document, with no Chinese attributive phrases. |
| X3 | Satisfied: no violation | Lines 10–12 and 20–21: no statement was reduced to sentence fragments or keywords. |
| X6 | Satisfied: no violation | Lines 3–8: the original table compares the same fields across four settings; no narrative was forced into a new table. |
| X7 | Satisfied: no violation | Lines 1–21: no folding or hidden primary content. |
| X8 | Satisfied: no violation | Lines 1–21: no repetitive template headings or filler sections. |

Additional X-group checks complete the anti-pattern review:

| Rule | Result | Evidence |
|---|---|---|
| X1 | No violation; 0 deduction | No emoji in source or output. |
| X2 | No violation; 0 deduction | One original heading across 21 output lines; no tiny added sections. |
| X4 | Machine pass, with additional preservation review | Format verifier exits 0 with no warnings/unknowns; exact reverse transformation and ordered-byte checks pass; facts and conditions mapped above. |
| X5 | No violation; 0 deduction | Only two phrases are bold; the audit raises neither T2 nor X5. |

The script still leaves its 32 judge rules unscored. This report records a manual disposition for all 32, with no pending manual unknowns. The recorded unmet content rules remain unmet; neither the script score nor successful preservation verification is presented as universal compliance.
