Revision completed with scope=content and level=deep (3), using `.agents/skills/adhd-md/SKILL.md`. The revised runbook is `output.md`; `input.md` was left unchanged. The requested output path takes precedence over the skill's default naming convention. This directory is not a Git repository.

**Checks**

Script score: **87.8 → 100.0 (+12.2)**. This is the deterministic script score, not a complete quality score or proof of semantic equivalence. Judge-rule decisions appear below; the document does not satisfy every deep-level rule.

| Dimension | Before | After | Delta |
|---|---:|---:|---:|
| First-screen clarity | 40.0 | 100.0 | +60.0 |
| Chunk size | 92.0 | 100.0 | +8.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Formatting consistency | 100.0 | 100.0 | 0.0 |
| Natural language | 100.0 | 100.0 | 0.0 |

- `verify --scope=content`: **pass**, exit 0; no hard failures, warnings, or unknowns. This checks the skill's declared invariants, not every possible change in meaning.
- Separate layout comparison: **pass**. Both files have 10 lines, the same blank lines, one H1, two paragraphs, and one four-item ordered list. Block order, heading level, list markers, emphasis, and folding structure are unchanged.
- Content findings: 1 → 0. Full-document findings: 2 → 0. The original H1 summary finding and P1 paragraph-length finding cleared through wording changes within the existing blocks.
- X-group script penalty: 0 → 0. Manual X-group review also found no violations.
- M-group findings: 0 → 0; no increase.
- Coverage at content/deep: 46 rules, comprising 20 script checks, 3 advisory rules, 22 judge rules, and 1 hard gate. The audit also lists format-axis judge rules because its score covers all axes; all 32 returned judge IDs are accounted for below.
- `fmt` was skipped because scope=content. Format-only verification would reject intentional wording changes, so content verification and a separate layout comparison were used.

Commands executed:

```sh
python3 .agents/skills/adhd-md/scripts/adhd_md.py audit input.md --level 3 --scope=content
python3 .agents/skills/adhd-md/scripts/adhd_md.py audit output.md --level 3 --scope=content
python3 .agents/skills/adhd-md/scripts/adhd_md.py verify input.md output.md --scope=content --json
python3 .agents/skills/adhd-md/scripts/adhd_md.py report input.md output.md --scope=content --level=3
python3 .agents/skills/adhd-md/scripts/adhd_md.py report input.md output.md --scope=content --level=3 --json
```

The JSON report, layout comparison, and M-group counts are saved in `output.checks.json`.

**Changes**

- Reworded the title and opening to state the task and its four-step extent.
- Joined the related session-setting statements within the existing introductory paragraph, retaining both facts and the archived-job prohibition.
- Added plain-text “Step X of 4” labels to the existing list items.
- Split the compound instructions into sentences within their original items. In step 2, “In that case” keeps the reload conditional on the active lock; “after the wait” retains the sequence.
- Made the existing success criterion actionable with “Check the request status.” The source's accepted-status statement and rendering caveat remain verbatim.

**Deliberately unchanged**

- The layout and four-item list remain intact. Deep editing does not override the content-only boundary.
- The wait remains exactly 7 minutes, followed by exactly one reload in the active-lock branch. No lock-clearing claim, extra retry, or unconditional reload was added.
- Manual settings remain limited to this browser session; the restriction was not generalized to all settings or to a device.
- Warnings about archived jobs, settings transfer, and rendering completion retain their negative wording.
- No task-duration estimates, UI confirmations for steps 1–3, or additional post-rendering actions were invented.

**Information-preservation review**

Each original fact, condition, restriction, and action was matched to the output. Line references below refer to the files on disk.

| Original information | Input location | Output location and review |
|---|---|---|
| The procedure retries a thumbnail job | input.md:1, input.md:3 | output.md:1, output.md:3; purpose retained, failed-job scope made explicit from the original selection step. |
| Only manual retry settings have the stated scope | input.md:3 | output.md:3; “Manual retry settings” retained. |
| Those settings apply only to this browser session | input.md:3 | output.md:3; same browser-session boundary. |
| Signing in elsewhere does not copy those manual settings | input.md:3 | output.md:3; same subject, action, and negation. |
| Do not retry jobs marked archived | input.md:3 | output.md:3; warning retained verbatim. |
| Open the job panel, then select a failed job | input.md:5 | output.md:5; both actions and their order retained. |
| The selected job's active lock controls the wait and reload | input.md:6 | output.md:6; both actions remain in that conditional branch. |
| Wait exactly 7 minutes | input.md:6 | output.md:6; value and unit unchanged. |
| Reload the panel once, after waiting | input.md:6 | output.md:6; object, count, and sequence retained. |
| Copy the job key into the incident note | input.md:7 | output.md:7; key and destination retained, before submission. |
| Submit the retry request | input.md:8 | output.md:8; unchanged action. |
| A successful request shows status accepted | input.md:10 | output.md:10; retained verbatim. |
| Accepted does not mean rendering has finished | input.md:10 | output.md:10; retained verbatim; no claim that rendering is necessarily still running. |

**Judge-rule decisions**

“Not applicable” identifies an absent trigger or a format-only rule outside this edit's scope. X-group rules were also inspected for regressions regardless of scope. No decision is left unreviewed.

| Rule | Decision | Location and reason |
|---|---|---|
| S4 | Satisfied | output.md:1 names the concrete task, “Retry a failed thumbnail job.” |
| S5 | Not applicable | output.md:1–10; moving existing blocks is a format action. No blocks were moved. |
| S6 | Not applicable | output.md:1–10; skeleton reordering is outside content scope. The existing purpose/constraints → procedure → result order remains. |
| S8 | Satisfied | output.md:3 states what the sole section lets the reader do. |
| H3 | Satisfied | output.md:3 states the reader's task: retry a failed thumbnail job. |
| H4 | Satisfied | output.md:3 gives “four steps,” counted directly from the existing list. No reading or execution duration was guessed. |
| P2 | Not applicable | output.md:3 and output.md:10; paragraph restructuring is outside scope. Existing paragraphs remain task prerequisites and result interpretation. |
| P5 | Not applicable | output.md:1–10 contains no quotation blocks. |
| L2 | Not applicable | output.md:3; converting the paragraph to a list would change the required layout. |
| L4 | Satisfied | output.md:5–8 use consistent progress labels and present-tense imperatives; the conditional step retains its required qualifier. |
| L7 | Satisfied | output.md:5–8 retain complete instructions with actions and objects. |
| W2 | Satisfied | output.md:3–10 uses active statements and direct imperatives. |
| W3 | Not applicable | output.md:1–10 has no parenthetical insertions. |
| W5 | Not applicable | output.md:1–10 has no unexplained abbreviations. The source's status explanation remains at output.md:10; no unsupported domain definitions were added. |
| W7 | Satisfied | output.md:5–8 and output.md:10 address the reader through direct imperatives and concrete verbs. |
| W8 | Satisfied | output.md:3–10 has no deeply nested clauses; compound actions were separated into sentences. |
| W9 | Satisfied | output.md:3 and output.md:10 retain necessary negative warnings and limitations, as the rule permits. |
| A1 | Satisfied | output.md:10 supplies the final action, “Check the request status,” followed by the sourced criterion and caveat. |
| A2 | Not satisfied | output.md:5–8; only the conditional 7-minute wait has a sourced duration. The source gives no duration estimates for the other actions. |
| A3 | Not applicable | output.md:5–8 offers one procedure, without competing options requiring a recommendation. |
| A5 | Not applicable | output.md:1–10 is a short runbook; a long-document shortcut is unnecessary and could imply that required steps may be skipped. |
| A6 | Satisfied | output.md:3 excludes archived jobs; output.md:6 ties waiting and reloading to an active lock. |
| A7 | Not satisfied | output.md:10 supplies the accepted-status criterion for step 4. Steps 1–3 lack explicit source-backed completion results or verification methods; the active-lock condition determines a branch, not proof that the reload succeeded. No missing results were invented. |
| A8 | Not satisfied | output.md:5–6 separates actions into sentences, as allowed for content edits, but each numbered item still contains two actions. Strict one-action-per-numbered-step compliance would require changing the preserved list structure. |
| N4 | Not applicable | output.md:1–10 contains no optional deep material; adding folds would also change formatting. |
| N7 | Satisfied | output.md:5–8 labels every existing step “Step X of 4” using plain text. |
| T3 | Not applicable | output.md:1–10 has no emphasis or inline-code markers; no marking style was added. |
| C4 | Not applicable | output.md:1–10 is English, so the Chinese modifier rule does not apply. |
| X3 | Satisfied | output.md:5–8 contains complete instructions rather than fragments or keyword lists. |
| X6 | Satisfied | output.md:1–10 contains no tables; narrative was not forced into cells. |
| X7 | Satisfied | output.md:1–10 contains no folds; all required actions remain visible. |
| X8 | Satisfied | output.md:1–10 contains no repeated empty headings or template sections. Progress labels provide actual step positions. |

The remaining X-group checks were also reviewed individually:

| Rule | Decision | Location and reason |
|---|---|---|
| X1 | Satisfied | output.md:1–10; no emoji. Script reports no hit. |
| X2 | Satisfied | output.md:1–10; one section and the original block structure. Script reports no fragmentation. |
| X4 | Satisfied | input.md:1–10 → output.md:1–10; content verification passed, and the information map above preserves all source statements, conditions, and sequencing. Machine verification alone is not the basis for this decision. |
| X5 | Satisfied | output.md:1–10; no bold text. Script reports no hit. |

A2, A7, and strict A8 remain unmet for the stated source and scope reasons. The 100.0 script score must not be read as full deep-level compliance.
