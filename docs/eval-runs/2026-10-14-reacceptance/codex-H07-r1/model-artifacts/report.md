# Rewrite report

Used `scope=content`, `level=standard` (`--level 2`). The English README rewrite is in [output.md](output.md). `input.md` was not overwritten. The [machine report](report.json) records the scores, coverage, findings, and verification result.

The script score is **100.0 → 100.0 (+0.0)**. This is not a complete rule score or a claim that every rule is satisfied. The script scores all applicable axes even when findings and coverage are filtered to `content`.

| Dimension | Before | After | Delta |
|---|---|---|---|
| First-screen clarity | 100.0 | 100.0 | +0.0 |
| Chunking | 100.0 | 100.0 | +0.0 |
| Scannability | 100.0 | 100.0 | +0.0 |
| Sentence load | 100.0 | 100.0 | +0.0 |
| Actionability | 100.0 | 100.0 | +0.0 |
| Formatting consistency | 100.0 | 100.0 | +0.0 |
| Natural language | 100.0 | 100.0 | +0.0 |

Anti-pattern deductions: **0 → 0**; script X hits: none. M-group findings: **0 → 0**. Content findings: **0 → 0**. The one unchanged full-document finding is N3, an advisory about a missing section divider; it is outside the requested content scope and carries no deduction.

`verify(content)` returned **pass**, exit code 0: no hard failures, warnings, or unknowns. This covers the verifier's declared checks, not a general proof of semantic equivalence. Manual comparison and an independent review also checked source facts, qualifiers, action order, and the content-only boundary. No `unknown` result has been treated as a pass.

Commands run:

```sh
python3 .agents/skills/adhd-md/scripts/adhd_md.py audit input.md --level 2 --scope=content
python3 .agents/skills/adhd-md/scripts/adhd_md.py audit output.md --level 2 --scope=content
python3 .agents/skills/adhd-md/scripts/adhd_md.py verify input.md output.md --scope=content --json
python3 .agents/skills/adhd-md/scripts/adhd_md.py report input.md output.md --scope=content --level 2
python3 .agents/skills/adhd-md/scripts/adhd_md.py report input.md output.md --scope=content --level 2 --json
```

## Changes and deliberate limits

The retention fact now appears in the main heading. The other headings identify the four-step task and summarize size and expiry behavior. Sentences are shorter, and each existing numbered item has a plain-text progress label. The four-step count comes directly from the source list; no time estimate or product behavior was invented.

Deliberately unchanged: heading levels, two prose paragraphs, four numbered items, four bullets, the existing bold UI path, and the original ordering of actions. No formatting pass was run. The combined check-and-download action remains within item 3 because content scope forbids adding a list item. The conditional empty-archive instruction also remains intact. Success messages, comparison criteria, and acronym definitions were not added because the source does not supply them.

## Rules left unjudged by the script

The script lists **23 unscored judgment rules** across all axes:

S4, S5, H4, P2, P5, L2, L4, L7, W2, W3, W5, W8, A1, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8.

The content-scope coverage reports 37 applicable rules: 19 script checks, 3 advisory-only rules, 14 judgment rules, and 1 hard gate. Its 14 judgment rules are S4, H4, L4, L7, W2, W3, W5, W8, A1, A7, A8, N7, C4, and X3. These counts are the script's coverage categories; language-specific rules can still be inapplicable on manual review.

The table records manual judgments for every rule in the script's unscored list. Locations refer to `output.md`. No listed rule was silently counted as a pass. L4, W5, A7, and A8 remain unmet, so full rule compliance is not claimed.

| Rule | Manual status | Location and reason |
|---|---|---|
| S4 | Satisfied | Lines 1, 7, 14 state retention, the four-step task, and size/expiry behavior. |
| S5 | Not applicable | Format-axis block relocation is outside content scope; the opening is rewritten in place. |
| H4 | Satisfied | Line 7 states 4 steps, counted from the existing list; no unsupported duration. |
| P2 | Satisfied, observed only | Lines 3 and 5 separately cover archive eligibility and its distinction from the recycle bin. Paragraph structure is unchanged. |
| P5 | Not applicable | No blockquotes in either document. |
| L2 | Not applicable | No prose-to-list conversion performed; format changes are outside scope. |
| L4 | Not met | Lines 9–12 use parallel imperative actions, but lines 16–19 retain a mix of factual statements and a conditional instruction. Clear conditions take priority over forcing uniform openings. |
| L7 | Satisfied | All items at lines 9–12 and 16–19 retain complete actions or factual statements. |
| W2 | Satisfied | Active language predominates; the passive “are split” at line 16 preserves a source statement without inventing an actor. |
| W3 | Not applicable | No parenthetical insertions. |
| W5 | Not met | ZIP and GB at lines 11 and 16 have no source-provided definitions. They remain unchanged; no explanation was invented. |
| W8 | Satisfied | Sentences have no stacked subordinate clauses; the conditional at line 19 remains explicit. |
| A1 | Satisfied | Line 12 gives the concrete final action: keep the ZIP in an approved project folder. Line 19 supplies the conditional troubleshooting action. |
| A7 | Not met | Lines 9–12 lack source-supported per-step success outputs. Line 11 names date and row count checks, but the source gives no comparison values or success criteria. |
| A8 | Not met: scope limit | Line 11 still combines checking and downloading under one number. Line 19 retains checking before a potential export request within the empty-archive condition. Splitting sentences does not make either a single-action item. |
| N4 | Not applicable | This short README has no separate optional material requiring folding; adding folding is outside scope. |
| N7 | Satisfied | Lines 9–12 each say “Step X of 4” within the existing numbered items. |
| T3 | Satisfied, observed only | Line 9 preserves the sole bold span for the UI path; no new emphasis style. |
| C4 | Not applicable | English document; Chinese modifier rule does not apply. |
| X3 | Satisfied: no violation | Lines 9–12 and 16–19 are complete statements, not fragments. |
| X6 | Satisfied: no violation | No tables in the rewritten README. |
| X7 | Satisfied: no violation | No collapsed content; all instructions remain visible. |
| X8 | Satisfied: no violation | No repeated filler headings or empty template sections. |

## Anti-pattern review

| Rule | Result | Evidence |
|---|---|---|
| X1 | No hit | No emoji; the existing UI arrow at line 9 is preserved. |
| X2 | No hit | Same 19 lines, 7 parsed blocks, and 3 heading positions; script reports no fragmentation. |
| X3 | No hit | Every list item remains meaningful on its own. |
| X4 | No detected loss | `verify(content)` passes; the manual preservation checklist below also matches. |
| X5 | No hit | Exactly the original bold span; no added emphasis. |
| X6 | No hit | No narrative content converted to a table. |
| X7 | No hit | No folding or hidden main-path content. |
| X8 | No hit | Headings contain source facts or the counted task length, without template filler. |

## Preservation checklist

| Source requirement | Output location and check |
|---|---|
| Completed exports retained for 14 days | Line 1; exact number and unit retained. |
| Only workspace owners can access archive | Line 3; exclusivity retained. |
| Files that failed before upload excluded | Line 3; before-upload qualifier retained. |
| Archive separate from recycle bin | Line 5. |
| Deleting archived export does not delete source records | Line 5; negation retained. |
| Open the exact bold UI path; select a completed export from the list | Lines 9–10; same order and bold text. |
| Check both date and row count before downloading ZIP | Line 11; “Then” preserves the ordering. |
| Keep ZIP in approved project folder; it may contain customer data | Line 12; approval requirement and uncertainty retained. |
| Exports strictly larger than 2 GB split into numbered ZIP files | Line 16; strict threshold, units, numbering, and plurality unchanged. |
| Link expires 30 minutes after creation | Line 17; exact duration and starting event retained. |
| Workspace guests cannot view archive | Line 18; prohibition retained. |
| If archive empty, check selected workspace before requesting new export | Line 19, verbatim; condition and ordering unchanged. |
| Code blocks and link targets | None in the input or output; none added or removed. |

A separate structural comparison confirmed identical heading levels, paragraph positions, blank-line pattern, ordered-list numbers, bullet markers, and bold text. Each original number/unit pair occurs the same number of times. Added progress numbers refer only to the four existing list items.
