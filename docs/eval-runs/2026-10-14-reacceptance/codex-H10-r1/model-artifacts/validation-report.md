Rewrite saved to [output.md](output.md), using `scope=content`, `level=standard` (`--level 2`). The source, [input.md](input.md), was not overwritten.

The script score is **100.0 → 100.0 (+0.0)**. This is a script-only score, not a complete rule assessment. The script scores all applicable axes even when findings are filtered to content.

| Dimension | Before | After | Delta |
|---|---:|---:|---:|
| First-screen clarity | 100.0 | 100.0 | 0.0 |
| Chunking | 100.0 | 100.0 | 0.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Formatting consistency | 100.0 | 100.0 | 0.0 |
| Natural wording | 100.0 | 100.0 | 0.0 |

Anti-pattern deductions: **0 → 0**; script X-group hits: none. M-group findings: **0 → 0**. Content findings: **0 → 0**. The unchanged, out-of-scope N3 suggestion concerns adding a separator between sections; it does not deduct points.

**verify(content): pass.** Hard failures: 0; warnings: 0; unknowns: 0; `ok=true`. This covers the script's declared invariants, not a proof of semantic equivalence. The source-to-output review below separately checks the conditions and action order. No `unknown` result is counted as a pass.

Commands run with the local skill snapshot:

```sh
python3 .agents/skills/adhd-md/scripts/adhd_md.py audit input.md --level 2 --scope=content
python3 .agents/skills/adhd-md/scripts/adhd_md.py audit output.md --level 2 --scope=content
python3 .agents/skills/adhd-md/scripts/adhd_md.py verify input.md output.md --scope=content
python3 .agents/skills/adhd-md/scripts/adhd_md.py report input.md output.md --scope=content --level 2
python3 .agents/skills/adhd-md/scripts/adhd_md.py report input.md output.md --scope=content --level 2 --json
```

Final audit, verify, and report commands exited successfully. Machine results are saved in [validation-report.json](validation-report.json).

Changed: headings now state the prerequisite or recovery action; the first symptom and queue-check instructions use shorter sentences; each recovery item carries a progress label; ID is expanded on first use. The total of 5 steps is counted from the existing list, not an estimated duration.

Deliberately unchanged: heading levels, block order and types, three bullet items, five numbered items, emphasis and folding styles, and the final warning paragraph. The opening Scope paragraph remains verbatim because the verifier protects its full value. The conditional wait and refresh remain together in step 3. No commands, links, timings, or success signals were invented.

**Rules unjudged by the script**

Audit lists 23 rules as unscored across all axes. Content coverage includes 14 judge rules: S4, H4, L4, L7, W2, W3, W5, W8, A1, A7, A8, N7, C4, X3. The table records a separate judgment for every rule in the audit's full unscored list. These judgments do not change the script score. No manual judgment remains pending; unmet and inapplicable rules are not passes.

Locations below refer to output.md unless marked otherwise.

| Rule | Judgment | Evidence and reason |
|---|---|---|
| S4 | Met | Lines 1, 5, 13: headings state the task, prerequisite, and conditional recovery action. |
| S5 | Not applicable | Format axis; no block relocation was performed under content scope. |
| H4 | Met | Line 1: 5 steps, counted from the existing numbered list. No completion time is guessed. |
| P2 | Not applicable | Format axis; paragraph boundaries are preserved at lines 3, 11, 21. |
| P5 | Not applicable | No blockquotes in either file. |
| L2 | Not applicable | Format axis; the source already uses lists. No paragraph-to-list conversion. |
| L4 | Met | Lines 7–9 are declarative conditions; lines 15–19 use present-tense instructions, with explicit conditions where required. |
| L7 | Met | Lines 7–9 and 15–19 retain complete statements or instructions. |
| W2 | Met | Lines 15–19 use active instructions; no passive action instructions were introduced. |
| W3 | Not applicable | The short parentheticals at lines 1 and 15 do not exceed the rule's five-word threshold. |
| W5 | Not met | Line 15 expands ID. Specialized terms such as indexer and requeue remain undefined; the source provides no definitions to preserve or restate. |
| W8 | Met | Lines 7, 11, 16 split statements; line 17 has one conditional branch without nested clauses. |
| A1 | Met | Line 11 directs recovery or the write-failure runbook. Line 19 gives the final confirmation required before incident closure. |
| A7 | Not met | Lines 17–19 retain the source's queue/staleness conditions and final updated-value check. The source supplies no separate acceptance checks for the recorded identifiers or metric, or immediate requeue result. These gaps were not filled with invented outputs. |
| A8 | Not met — scope constraint | Line 16 still checks and saves; line 17 still waits and refreshes. Sentence splitting cannot make an existing numbered item a single action. Adding items would violate content scope. |
| N4 | Not applicable | Format axis; neither file has folded content, and the short runbook needs no optional appendix. |
| N7 | Met | Lines 15–19 each say Step X of 5 using plain text within the existing list items. |
| T3 | Not applicable | No emphasis or inline-code markers to reconcile; none were added. |
| C4 | Not applicable | The document is English. |
| X3 | Met | Lines 7–9 and 15–19 remain complete conditions and instructions, not fragments. |
| X6 | Not applicable | No tables in the runbook. |
| X7 | Not applicable | No folded content in the runbook. |
| X8 | Met | Lines 1, 5, 13 use specific headings; no repeated empty subsection template. |

Additional X-group review: X1 has no emoji; X2 has no fragmentation finding and retains the original 21-line, three-heading structure; X4 passes the declared invariant checks and the manual preservation review below; X5 has no bold text. X3, X6, X7, and X8 are addressed individually above. Zero X deductions does not imply that A7, A8, or W5 is satisfied.

**Preservation review**

| Source requirement | Output location and review |
|---|---|
| Dashboard search index only; excludes billing exports and direct database queries | Line 3, verbatim. |
| Record changed more than 5 minutes ago and dashboard shows its previous value | Line 7; strict greater-than boundary, number, unit, and both facts retained. |
| Record visible in primary database; no index maintenance in progress | Lines 8–9, verbatim. Heading and line 11 make the existing prerequisites explicit. |
| Missing database record routes to write-failure runbook instead | Line 11; exception retained. |
| Record workspace ID, record ID, and last update time | Line 15; all three fields retained. |
| Check indexer queue depth and save metric value | Line 16; both actions retained in order. |
| Only when queue is nonzero, wait 3 minutes, then refresh once | Line 17; the same condition controls both actions. Duration, unit, order, and single refresh retained. |
| If value is still stale, requeue only affected workspace | Line 18; condition and workspace restriction retained. |
| Updated value must appear before incident closure | Line 19; closure prerequisite retained. |
| No global-index rebuild during business hours | Line 21, verbatim. |
| Requeueing does not modify primary database | Line 21, verbatim. |
| Original numbered sequence 1–5 | Lines 15–19; all five items retain their order and numbering. New progress counts are derived from this list. |
| Code blocks and link targets | Neither exists in the input or output. The write-failure runbook reference remains plain text. |

The rewrite is delivered with the stated limitations. Full rule compliance is not claimed.
