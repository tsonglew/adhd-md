# Reformatting report

Applied `scope=format`, `level=standard` (`--level 2`) using `.agents/skills/adhd-md/SKILL.md`. The English meeting note is saved as `output.md`; `input.md` was not overwritten.

Only Markdown markers and layout whitespace changed. All original wording, punctuation, numbers, units, conditions, exceptions, and information order are retained. The source contains no links or code blocks.

## Commands and exit status

All commands used `python3 .agents/skills/adhd-md/scripts/adhd_md.py`.

| Arguments | Exit status | Result |
|---|---:|---|
| `audit input.md --level 2 --scope=format` | 0 | Script score 81.2; X2 deduction 8 |
| `fmt input.md` | 0 | Preview found no deterministic fixes; no write requested |
| `audit output.md --level 2 --scope=format` | 0 | Script score 100.0; no findings |
| `verify input.md output.md --scope=format` | 0 | `pass` |
| `report input.md output.md --scope=format --level=2` | 0 | Before/after comparison and verification |
| `report input.md output.md --scope=format --level=2 --json` | 0 | Saved as `output.report.json` |

Verification reports zero hard failures, warnings, or unknowns. `pass` covers the verifier's declared checks, not a general proof of semantic equivalence. No `unknown` result has been counted as a pass.

## Script score

**81.2 → 100.0 (+18.8)**. These are script scores, not complete rule scores; the JSON score band remains `null`.

| Dimension | Before | After | Delta |
|---|---:|---:|---:|
| First-screen conclusion | 40.0 | 100.0 | +60.0 |
| Chunking | 100.0 | 100.0 | 0.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Typography consistency | 100.0 | 100.0 | 0.0 |
| Natural expression | 100.0 | 100.0 | 0.0 |

Anti-pattern deductions: **8 → 0**. Before: X2, from heading density and short average prose sections. After: no X-group script hits. The conclusion already appeared first in the source; the first-screen score change reflects the script's recognition of the reformatted blocks, not new content.

Format findings: 5 → 0. All-axis findings: 6 → 0. M-group findings: 0 → 0. Scope filters displayed findings and coverage; the script score still includes all applicable axes.

## Unjudged rules and manual review

The script leaves these 23 rules unscored: **S4, S5, H4, P2, P5, L2, L4, L7, W2, W3, W5, W8, A1, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8**. They are not automatic passes. Each is reviewed below; manual judgments have not been added to the numeric script score.

Format coverage: 39 applicable rules; 23 script-checked, 4 advisory, 9 requiring judgment, 2 automatic-format-only, and 1 verification gate. The 9 format judgment rules are S5, P2, P5, L2, N4, T3, X6, X7, and X8. Content rules below are reviewed for disclosure; this task does not authorize changing their wording.

Locations below refer to `output.md`.

| Rule | Manual status | Evidence and reason |
|---|---|---|
| S4 | Not satisfied; content scope limitation | Lines 1, 3, 9, 15, 20: original topic-based title and labels retained. Rewriting them as conclusions would change wording. |
| S5 | Satisfied | Lines 3–7: the rollout outcome remains first, before decisions and actions. |
| H4 | Not satisfied; content scope limitation | Lines 1–15: no reading-time or length estimate. The meeting date and task deadlines are not reading estimates. Adding one would add content. |
| P2 | Satisfied | Lines 5–7 separate individual metrics; lines 22 and 24 separate the conditional rollback action and its exception. |
| P5 | Not applicable | Lines 1–24 contain no quotation blocks. |
| L2 | Satisfied | Lines 5–7 list the three existing outcome sentences in order; decision and action lists remain intact. |
| L4 | Satisfied | Lines 5–7 use declarative metrics; lines 11–13 use directives; lines 17–18 use owner-and-action structure. |
| L7 | Satisfied | Lines 5–18 retain complete statements, directives, conditions, and task details. |
| W2 | Satisfied | Lines 5–24 use active or copular constructions, without passive-voice instructions. |
| W3 | Not applicable | Lines 1–24 contain no parenthetical insertions. |
| W5 | Not applicable | Lines 1–24 contain no introduced technical acronym requiring expansion; `ms` is a retained measurement unit. |
| W8 | Satisfied | Lines 11–13 and 22 retain simple conditions without deeply nested clauses. |
| A1 | Satisfied | Lines 17–18 give named owners, concrete tasks, and deadlines; line 22 gives the conditional rollback action. |
| A7 | Not satisfied; source and scope limitation | Lines 13, 17–18, and 22 state actions and deliverables but do not consistently supply a distinct completion check or expected verification result. No additional success criteria or validation behavior is supplied by the source. |
| A8 | Satisfied | Lines 17–18 each assign one action. Line 22 has one conditional rollback action; the condition does not create an extra action. |
| N4 | Not applicable | Lines 1–24 are short, core meeting information, with no optional background needing folding. |
| N7 | Not applicable | Lines 17–18 contain two independent tasks, not a sequential workflow of at least four steps. |
| T3 | Satisfied | Lines 3, 9, 15, 20 consistently use bold for existing section labels. Checkboxes remain task markers. |
| C4 | Not applicable | The note is English; the Chinese modifier rule does not apply. |
| X3 | Satisfied; no violation | Lines 5–18 retain meaningful sentences and complete directives, rather than isolated keywords. |
| X6 | Not applicable; no violation | The output contains no tables. |
| X7 | Not applicable; no violation | The output contains no folded or hidden content. |
| X8 | Satisfied; no violation | Lines 3, 9, 15, 20 reuse the four original meaningful labels, with no added template headings or filler. |

The remaining X-group checks were also reviewed: X1 has no emoji; X2 now has one H1 and compact labels with no blank-line padding; X4 passes format verification and exact reconstruction of the source; X5 has only four short bold labels and no density finding. X-group deductions are zero, but the unmet content rules above prevent a claim that every rule is satisfied.

## Preservation review

| Original information | Output location |
|---|---|
| Meeting title and `2026-09-22` | Line 1 |
| Rollout reached `100%` of workspaces | Line 5 |
| Median `210 ms`; target below `250 ms` | Line 6 |
| 95th percentile `680 ms`, above target `600 ms` | Line 7 |
| Keep rollout at `100%` while error rate stays below `0.5%` | Line 11 |
| Do not enable fuzzy matching until below `600 ms` for three consecutive days | Line 12 |
| Recheck mobile separately; desktop data does not cover it | Line 13 |
| Alex adds mobile latency to dashboard by Friday | Line 17 |
| Search team reports three daily percentile values next week | Line 18 |
| Error rate exceeds `1%` for `10 consecutive minutes` → previous index version | Line 22 |
| A single slow query is not a rollback trigger | Line 24 |

Reversing only the explicitly introduced formatting changes reconstructs the original UTF-8 bytes exactly. The unchanged input SHA-256 is `77dd7a37c78da1630d15de0a28c02505b012d236ce79bb0431ddfc8bbcdfd2cc`.

## Changes and deliberate preservation

Changed four H2 headings to bold labels, made the three existing outcome sentences a list, and separated the rollback exception into its own paragraph. The unique H1 remains.

Deliberately retained all wording, punctuation, thresholds, strict comparisons, timing conditions, owners, deadlines, decision bullets, action checkboxes, and information order. No summary, reading estimate, explanatory text, verification method, link, or code block was added to the document.
