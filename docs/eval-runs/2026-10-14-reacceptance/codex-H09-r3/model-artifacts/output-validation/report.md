# Formatting validation

Created [output.md](../output.md) from [input.md](../input.md), using the case's `.agents/skills/adhd-md/SKILL.md`: English reference document, `scope=format`, `level=deep` (`3`). The input was not overwritten.

Changed two prose paragraphs into two lists of complete, unchanged sentences. Added bold emphasis to “never retried” and “after the worker restarts”. All edits insert Markdown characters only. Removing those recorded insertions recovers the original UTF-8 bytes exactly, including spaces and punctuation, in their original order.

Deliberately unchanged: the title, parameter table, defaults, ranges, units, YAML fence and body, conditions, exceptions, wording, and information order. No summary, estimate, labels, headings, links, procedural instructions, or success output were added. No content was hidden. Deep-level review does not override these constraints.

| Command | Exit status | Result |
|---|---:|---|
| `audit input.md --level 3 --scope=format --json` | 0 | Script score 100.0; no findings |
| `audit output.md --level 3 --scope=format --json` | 0 | Script score 100.0; no findings |
| `verify input.md output.md --scope=format --json` | 0 | `pass`; no hard failures, warnings, or unknowns |
| `report input.md output.md --scope=format --level=3 --json` | 0 | Comparison generated; verification `pass` |

Commands use `python3 .agents/skills/adhd-md/scripts/adhd_md.py`. Exact commands and statuses are saved in [exit-statuses.json](exit-statuses.json). The initial text audit also exited 0. The non-writing `fmt input.md` preview exited 0 and proposed no changes. The candidate passed verification before delivery. `diff` exited 1 because the expected formatting differences exist; that is not a validation failure. The preliminary Git status check exited 128 because this directory is not a Git repository; the explicit separate-output instruction was followed.

**Script score: 100.0 → 100.0 (delta 0.0).** This is not a complete quality score or a claim that all rules pass. The script scores across all axes even though findings and coverage are filtered to format scope.

| Script dimension | Before | After | Delta |
|---|---:|---:|---:|
| First-screen usefulness | 100.0 | 100.0 | 0.0 |
| Chunking | 100.0 | 100.0 | 0.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Typography consistency | 100.0 | 100.0 | 0.0 |
| Naturalness | 100.0 | 100.0 | 0.0 |

**Anti-pattern deductions: 0 → 0.** No script X-group hits before or after. Manual review also found no X3, X6, X7, or X8 violations. M-group findings remain 0 → 0.

Change counts: 18 → 21 lines; 2 prose paragraphs → 2 lists containing the same 5 sentences; 0 new sentences, 0 moved blocks, 0 folded blocks, 0 new headings. One table and one YAML block remain unchanged.

Verification covers the skill's declared machine checks; `pass` is not a general semantic-equivalence proof. The additional [preservation record](preservation.json) establishes exact recovery of every original byte and unchanged order for this particular edit. Manual comparison confirms that the retry exception and restart condition remain attached to their original statements. No original links exist to modify. No `unknown` result was treated as a pass.

The audit leaves **32 rules unjudged by the script**, of which **10 are in the selected format scope**. Format coverage is 41 rules: 23 script-checked, 5 hint-only, 10 judgment-only, 2 formatter-only, and 1 verification gate. The script's unjudged list remains unscored; the following separate review records all 32. “Not applicable” does not mean “passed”. No complete combined numerical score or overall all-rules-pass claim is made.

| Rule | Manual judgment | Output location and reason |
|---|---|---|
| S4 | Not met; outside format scope | Line 1 is a topic title. Changing its wording is prohibited. |
| S5 | Met | Lines 3–8 put the lookup answers first; no block movement is needed. |
| S6 | Met | Lines 3–21 retain the reference structure: parameter table, behavior notes, example, and remaining notes. |
| S8 | Not met; outside format scope | Lines 1–3 have no opening purpose sentence. Adding one is prohibited. |
| H3 | Not met; outside format scope | Lines 1–15 have no explicit reader-outcome statement. No statement was invented. |
| H4 | Not met; scope and character constraints | Lines 1–15 contain no reading-time or length estimate. This rule also applies to references, but adding text is prohibited. |
| P2 | Met | Lines 10–12 and 20–21 separate independent facts while keeping each condition intact. |
| P5 | Not applicable | Lines 1–21 contain no quotation block. |
| L2 | Met | Lines 10–12 and 20–21 present the original statements as two short lists. |
| L4 | Met on review; outside format scope | Lines 10–12 and 20–21 retain declarative statements with noun or identifier subjects. |
| L7 | Met on review; outside format scope | Each item at lines 10–12 and 20–21 remains a complete sentence, not a fragment. |
| W2 | Not met; outside format scope | Passive descriptions remain at lines 12 and 21, among others. Rewording is prohibited. |
| W3 | Met on review; outside format scope | Line 12 preserves the short parenthesis “401 and 403”; it does not exceed five words. |
| W5 | Not applicable | Lines 3–8 explain the setting identifiers; there is no unexplained prose acronym. |
| W7 | Not applicable to this descriptive reference | Lines 3–21 describe settings and behavior rather than addressing the reader with instructions. |
| W8 | Met on review; outside format scope | Lines 10–12 and 20–21 contain no three-level nested clause structure. |
| W9 | Met under the exception allowance; outside format scope | Line 12 preserves the necessary “never retried” exception. Converting that negation would risk changing meaning. |
| A1 | Not met under the rubric's code-section trigger; outside format scope | Lines 14–21 contain a YAML example and descriptive activation timing, but no explicit next-action instruction. No instruction was added. |
| A2 | Not applicable | Lines 14–21 provide a configuration example and notes, with no timed procedural steps. |
| A3 | Not applicable | Lines 3–8 list parameter defaults, not alternative workflows requiring a recommendation and rationale. |
| A5 | Not applicable | The whole output is a short, 21-line lookup reference, not a long document needing a single-action entry point. |
| A6 | Not applicable | Lines 3–21 describe configuration behavior; there is no action-selection decision point. |
| A7 | Not applicable to procedural-step checking; source gap retained | Lines 14–18 are a configuration example, not an executable step. The source supplies no success output or test; none was invented. This is not an A7 pass claim. |
| A8 | Not applicable | Lines 10–12 and 20–21 are facts, not compound action steps. The YAML keys are configuration data. |
| N4 | Not applicable | Lines 3–21 are core lookup information; there is no optional deep section to fold. |
| N7 | Not applicable | Lines 1–21 contain no process of four or more steps. The five factual bullets are not a workflow. |
| T3 | Met | Lines 3–21 retain code formatting for literal identifiers/values and use two bold spans for important behavioral constraints. |
| C4 | Not applicable | The document is English. |
| X3 | Met: no violation | Lines 10–12 and 20–21 retain all sentence text and complete assertions. |
| X6 | Met: no violation | Lines 3–8 preserve an appropriate four-column comparison table; no narrative was forced into cells. |
| X7 | Met: no violation | Lines 1–21 contain no folds or hidden core information. |
| X8 | Met: no violation | Line 1 is still the sole heading; no boilerplate sections were added. |

The remaining X rules were explicitly checked: X1 has no emoji; X2 has no added headings or fragmented sections; X4 passes machine verification plus exact original-byte recovery; X5 has no over-bolding finding and only two short emphasis spans. All X deductions remain zero. H4 and the other recorded unmet content rules prevent any claim of universal deep-level compliance.

Raw evidence: [before audit](audit-before.json), [after audit](audit-after.json), [verification](verify.json), [script comparison](report.json), and [preservation check](preservation.json).
