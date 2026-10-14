Applied scope=content, level=deep (3), using [.agents/skills/adhd-md/SKILL.md](.agents/skills/adhd-md/SKILL.md). The revised runbook is [output.md](output.md); the original [input.md](input.md) is unchanged. The requested output path takes precedence over the skill's default naming. This directory is not a Git repository.

The script score increased from 87.8 to 100.0 (+12.2). This is a script-only score, not a claim that every rule is satisfied. A2, A7, and A8 remain unmet for the reasons below.

| Dimension | Before | After | Delta |
|---|---:|---:|---:|
| First-screen clarity | 40.0 | 100.0 | +60.0 |
| Chunk size | 92.0 | 100.0 | +8.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Formatting consistency | 100.0 | 100.0 | 0.0 |
| Natural language | 100.0 | 100.0 | 0.0 |

**Checks performed**

- Ran the initial audit with `--level 3 --scope=content` before editing. It reported H1; the full findings also included P1. Both are absent after the rewrite.
- Ran `verify input.md output.md --scope=content`: pass, with no hard failures, warnings, or unknowns.
- Ran text and JSON reports with `--scope=content --level=3`. The [JSON report](output.checks.json) records the final checks, scores, findings, and coverage.
- Checked parsed block types and positions, blank-line positions, heading level, list numbering, and the final newline: pass. Both files have 10 lines and four blocks: H1, paragraph, ordered list, paragraph. The list still has exactly four items; no emphasis or folding was added.
- Checked all four progress labels against the actual list length: pass.
- M-group findings stayed at 0. X-group script deductions stayed at 0; the manual X review below found no anti-pattern violations.
- Reviewed the source facts, restrictions, and action sequence against the output, as mapped below. The machine verifier checks defined invariants; it does not prove semantic equivalence or enforce every layout constraint.

The audit reports 46 applicable rules for deep/content: 20 script checks, 3 advisory rules, 22 judge rules, and 1 verification gate. Its script score still includes all applicable axes. The audit's full judge list contains 32 rules; every one is recorded below, including those outside content scope. No final combined numeric score is claimed. Formatting automation was skipped because scope=content.

**What changed**

- Reworded the topic heading as an action and made the opening state the task and its four-step length.
- Moved the archived-job prohibition earlier within the existing opening paragraph. Joined the two related settings statements with a semicolon, keeping the paragraph and all its facts.
- Added plain-text “Step X of 4” labels within the existing numbered items.
- Separated the actions in items 1 and 2 into sentences while keeping their order and conditional relationship.
- Turned the existing request-success description into an explicit instruction to check the status. Retained the source's exact status value, accepted, and its rendering caveat.

**Deliberately unchanged**

- Preserved the heading level, paragraph/list arrangement, blank lines, numbering, and absence of emphasis or folding. Deep mode does not override content-only scope.
- Kept compound items 1 and 2 in their original numbered items; adding steps or checkboxes would change the layout. Sentence splitting does not satisfy A8.
- Preserved the conditional 7-minute wait and single reload. Reloading follows that conditional wait; it is not an unconditional action or a repeated polling loop.
- Kept the settings restriction specific to manual retry settings and this browser session. Kept both negative warnings.
- Added no total-duration estimate, undocumented interface output, lock-release guarantee, retry-completion guarantee, escalation procedure, or missing step-verification criteria.

**Information-preservation review**

Line references below refer to the unchanged 10-line source and the 10-line output.

| Source information | Source | Output | Review |
|---|---|---|---|
| Procedure retries a thumbnail job; the selected job is failed | input.md:3,5 | output.md:1,3,5 | Preserved; no promise of completed rendering |
| Manual retry settings apply only to this browser session | input.md:3 | output.md:3 | Preserved; not generalized to all settings or devices |
| Signing in elsewhere does not copy those manual settings | input.md:3 | output.md:3 | Preserved explicitly |
| Do not retry jobs marked archived | input.md:3 | output.md:3 | Prohibition retained before the steps |
| Open the job panel, then select a failed job | input.md:5 | output.md:5 | Both actions and their order retained |
| If the selected job's lock is active, wait 7 minutes | input.md:6 | output.md:6 | Same condition, duration, and unit |
| Reload the panel once after that conditional wait | input.md:6 | output.md:6 | “After that wait” keeps reload dependent on the active-lock wait; no recheck or new branch added |
| Copy the job key into the incident note before submitting | input.md:7–8 | output.md:7–8 | Object, destination, and sequence retained |
| Submit the retry request | input.md:8 | output.md:8 | Preserved |
| A successful request shows status accepted | input.md:10 | output.md:10 | Same success indication; used as the status check |
| Accepted does not mean the thumbnail has finished rendering | input.md:10 | output.md:10 | Preserved verbatim |

The added count of 4 and the progress labels are directly countable from input.md:5–8. The added instruction to check status restates the validation already supplied in input.md:10. No new product behavior was introduced.

**Judge-rule decisions**

“Satisfied” means the output meets the rule; for X rules, it means the prohibited pattern is absent. “Not applicable” identifies either a scope exclusion or absent subject matter, not an assumed pass. Locations refer to output.md unless stated otherwise.

| Rule | Decision | Location and reason |
|---|---|---|
| S4 | Satisfied | Line 1 states the action, “Retry a failed thumbnail job,” instead of a topic label. |
| S5 | Not applicable | Lines 1–10: block relocation is a format operation; the existing block order is preserved. |
| S6 | Not applicable | Lines 1–10: the deep runbook skeleton is optional and format-scoped; new sections or checkboxes would conflict with the request. |
| S8 | Satisfied | Line 3 opens by saying what the procedure enables. There is only one section. |
| H3 | Satisfied | Line 3 states the reader's task: retry a failed thumbnail job. |
| H4 | Satisfied | Line 3 gives “4 steps,” counted from the original four items. No reading or execution time is invented. |
| P2 | Not applicable | Line 3: paragraph restructuring is outside content scope; the original opening paragraph remains one block. |
| P5 | Not applicable | Lines 1–10 contain no blockquotes. |
| L2 | Not applicable | Lines 3–8: conversion of prose into lists is format-scoped; the existing list is preserved. |
| L4 | Satisfied | Lines 5–8 use matching progress labels and imperative instructions; item 2 retains its necessary condition. |
| L7 | Satisfied | Lines 5–8 contain complete instructions with objects and conditions, not isolated keywords. |
| W2 | Satisfied | Lines 3–10 use active statements and imperative instructions. |
| W3 | Not applicable | Lines 1–10 contain no parenthetical insertions. |
| W5 | Not applicable | Lines 1–10 contain no acronyms needing first-use expansion. Source terms and status labels are retained without invented definitions. |
| W7 | Satisfied | Lines 3,5–8,10 address the reader through present-tense imperatives such as Use, Open, Copy, Submit, and Check. |
| W8 | Satisfied | Lines 3–10 contain no nested chains of subordinate clauses. The active-lock condition remains local to item 2. |
| W9 | Satisfied | Lines 3,10 retain necessary negative restrictions: archived jobs, settings not copied, and acceptance not proving completion. These qualify for the warning exception. |
| A1 | Satisfied | Line 10 gives the next action after submission: check the request status, using the source's success indicator. |
| A2 | Not satisfied | Line 6 preserves the known 7-minute conditional wait. The source supplies no durations for items 1,3,4 or the whole procedure; none were guessed. |
| A3 | Not applicable | Lines 5–8 offer no competing methods that need a default recommendation. |
| A5 | Not applicable | This is a short four-item procedure, not a long document needing a separate one-action entry point. |
| A6 | Satisfied | Lines 3,6 retain both decision criteria: archived jobs must not be retried; an active lock triggers the wait and subsequent single reload. |
| A7 | Not satisfied | Line 10 supplies the expected result for item 4. Input.md:5–7 supplies no explicit success output or verification method for items 1–3. The active-lock condition is a branch trigger, not proof of success. |
| A8 | Not satisfied | Lines 5–6 still contain two actions per numbered item: open/select and wait/reload. They are clearer sentences, but content-only scope prevents adding numbered items. |
| N4 | Not applicable | Lines 1–10 contain no optional deep material or folding; adding folding would be a format change. |
| N7 | Satisfied | Lines 5–8 each state “Step X of 4” in ordinary text within the original list. |
| T3 | Not applicable | Lines 1–10 have no emphasis or inline-code markers whose meanings need harmonizing. |
| C4 | Not applicable | The document is English, not Chinese. |
| X3 | Satisfied | Lines 5–8 preserve full instructions and their necessary objects and conditions. |
| X6 | Satisfied | Lines 1–10 contain no tables. |
| X7 | Satisfied | Lines 1–10 contain no folding; the entire procedure is visible. |
| X8 | Satisfied | Lines 1–10 add no boilerplate sections or empty template fields. Progress labels serve N7. |

**Remaining X-group checks**

| Rule | Decision | Evidence |
|---|---|---|
| X1 | Satisfied | output.md:1–10 contains no emoji; no script hit. |
| X2 | Satisfied | output.md:1–10 retains one heading and the original four blocks; no script hit. |
| X4 | Satisfied for declared checks and manual review | Content verification passed with no warnings or unknowns; every source fact and constraint is mapped above. This is not a claim of machine-proven semantic equivalence. |
| X5 | Satisfied | output.md:1–10 contains no bold text; no script hit. |
