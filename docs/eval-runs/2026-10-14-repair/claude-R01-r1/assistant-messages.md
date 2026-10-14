I'll start by reading the skill and the input file.

Now let me inspect how the script judges H1 and P1, so my rewrite actually clears them.

Verification passes on both scopes and the score moved 87.8 → 100.0. Here is the report.

## Done: `input.md` → `output.md`

**scope** `content` · **level** `deep` · written to `output.md`

The workspace is not a git repo, so the skill's default would be `input.adhd.md`; your instruction named `output.md`, so I wrote that and left `input.md` untouched (it is the verify baseline). `scope=content` → step 2 (`fmt`) was skipped by design.

**Script score 87.8 → 100.0 (+12.2)** — this is the script score only. 32 rules in this configuration need model judgment and the script counts them as "not hit"; it is not a final grade. My per-rule decisions are in the table below.

| Dimension | before | after | delta |
|---|---|---|---|
| First-screen conclusion (首屏结论力) | 40.0 | 100.0 | +60.0 |
| Chunking (分块粒度) | 92.0 | 100.0 | +8.0 |
| Scannability (扫读性) | 100.0 | 100.0 | 0 |
| Sentence load (句子负荷) | 100.0 | 100.0 | 0 |
| Actionability (行动性) | 100.0 | 100.0 | 0 |
| Typography (排版一致性) | 100.0 | 100.0 | 0 |
| Human feel (活人感) | 100.0 | 100.0 | 0 |

Anti-pattern deduction −0 → −0. Findings 2 → 0 (`H1` no first-screen conclusion, `P1` 4-sentence paragraph). M-group hits did not rise (0 → 0).

**verify** `--scope=content` **pass** (no hard failures, no warnings, no unknowns); `--scope=both` also pass. This covers the declared invariants only: code blocks, link targets, inline-code values, command options, paths, permission values, case-sensitive identifiers, and numeric/unit values are unchanged (no warnings raised). It is not a proof of semantic equivalence, and it says nothing about sentence-level meaning.

### What I changed
- Split the 4-sentence opening paragraph into a lead + a boundary paragraph (`output.md:3,5`); the lead is a new TL;DR sentence and the boundaries are the original sentences, verbatim.
- Lead line: "Retry a failed thumbnail job. The procedure has 4 steps, and one of them adds a 7-minute wait when the job's lock is active." — restates the source plus countable length (4 steps) and the source's own 7-minute wait. No total runtime invented.
- Step 1 split into two actions in-item: "Open the job panel. Select a failed job." (A8; no new list items — content scope).
- Step 2 branch split in-item: "If the job's lock is active, wait 7 minutes. When the wait is over, reload the panel once." The condition still controls both sub-actions, order kept, "once" kept, 7 kept.
- Step 4 gained the source's own success signal at the point of action: "Expected: status accepted." (A7 for that step).
- Progress labels `Step N of 4` in plain text inside the existing ordered items (N7; no headings, no checkboxes — content scope).

### Deliberately not changed
- **"Manual retry settings apply only to this browser session. Signing in elsewhere does not copy those manual settings."** — left verbatim. Rewriting risked generalizing "manual retry settings" to settings at large, or "browser session" to "device". This is the sharpest boundary in the file.
- **"Do not retry jobs marked archived."** — kept as a negative (W9's warning exception); kept as a plain sentence, not a `> **Warning**` blockquote, because that would be a layout change.
- **The closing pair of sentences** — verbatim. "Accepted" must not be flipped to "rendering is in progress"; the positive restatement "Expected: status accepted" sits in step 4 and the caveat stays where the source put it.
- **The H1** — `# Thumbnail recovery` unchanged, so **S4 is not met** (see table). Holding the title steady was a judgment call under "preserve the original layout style"; renaming is permitted by content scope but changes the runbook's identifier.
- **No expected output invented for steps 1–3**; no next step invented after step 4; no glosses for `job panel` / `job key` / `incident note` / `lock`. The source does not supply them, so those rules stay unmet rather than filled with fabricated UI behavior.
- **No new heading levels, no checkboxes, no `<details>`, no TOC, no tables, no bold/italic/code marks added.** Under `level=deep` the runbook skeleton would normally add step headings and checkboxes; `scope=content` forbids that and you asked to preserve the layout style, so the skeleton was applied only where it could be expressed as prose.

### Judge-rule decisions (32 rules)

Verdicts use the skill's four values: met（满足）/ not met（不满足）/ n/a（不适用）/ cannot judge（无法判断）. Locations are in `output.md` unless noted.

| Rule | Verdict | Basis |
|---|---|---|
| S4 title states the answer | **not met** | H1 kept as `# Thumbnail recovery` (topic-style). Deliberate: title is the doc's identifier and the layout was to be preserved. Optional alternative: `# Retry a failed thumbnail job`. |
| S5 conclusion first | met | Source's first sentence already was the conclusion; output keeps it first and sharpens it into the lead (`:3`). No block move, so no dangling reference. |
| S6 section order matches doc type | n/a | Runbook type, but the doc has no H2 sections and content scope forbids adding any; skeleton can't be applied without a layout change. |
| S8 section-opening sentence | n/a | No sections (single H1, paragraphs + one list). |
| H3 first screen says what you get | met | "Retry a failed thumbnail job." (`:3`) — reader payoff, not doc structure. |
| H4 time/length estimate | met | "has 4 steps, and one of them adds a 7-minute wait…" (`:3`). Length from the doc, duration from the source's own 7 minutes. No total invented. |
| P2 one topic per paragraph | met | `:3` what it does/how long · `:5` settings boundary + do-not-retry · `:11` success criteria. Original mixed 4 sentences into one paragraph. |
| P5 oversized quote block | n/a | No blockquotes. |
| L2 parallel clauses → list | n/a | No enumerable clause left; content scope also forbids changing list form. |
| L4 parallel list items | met | All four items open `Step N of 4 — ` + bare verb (Open/Select, wait/reload, Copy, Submit). |
| L7 items keep full meaning | met | Each item reads standalone; no keyword shrapnel (`:7–10`). |
| W2 active voice | met | All imperative/active; zero passive sentences. |
| W3 parenthetical asides | n/a | No parentheses. |
| W5 explain terms at first use | **not met** | `job panel`, `job key`, `incident note`, `lock` are undefined. Source gap — glossing them would mean inventing product behavior. |
| W7 you + present + concrete verbs | met | Imperatives carry second person; every verb is concrete and present tense. |
| W8 one clause per sentence | met | Longest sentence is a single-layer conditional (23 words); no nesting. |
| W9 negations → positive | met (exception held) | The two negations are warnings ("Do not retry jobs marked archived." `:5`; "Accepted does not mean the thumbnail has finished rendering." `:11`) and stay negative by rule. Flipping the second would assert something the source never says. |
| A1 next step at the end | **not met** | Doc ends on the success criterion, not a next action. The source never says what to do after submitting, so none was added. |
| A2 time estimate per step | **not met** (partly) | Only step 2 carries the source's 7 minutes; steps 1/3/4 have no basis and were not padded. |
| A3 default recommendation | n/a | No options to choose between; step 2 is a condition, not a choice. |
| A5 "do this one thing" | n/a | Deep-level rule aimed at long docs; this is a 12-line single-task runbook and the lead already carries the entry point. |
| A6 decision point gives its criterion | met | The only branch keeps its source criterion: "If the job's lock is active" (`:8`). |
| A7 expected output / verification | **not met** (1 of 4 steps) | Step 4 has the source's own signal at the action (`:10`), reinforced by `:11`. Steps 1–3 have no output, UI state, or check stated anywhere in the source — left unmet and reported rather than fabricated. |
| A8 one action per step | met | Step 1 → open / select; step 2 → wait / reload with the condition still governing both and the order intact; steps 3 and 4 were already single-action. Splitting done inside the existing items, no list items added. |
| N4 fold optional content | n/a | Nothing is off the main path; content scope forbids touching fold structure. |
| N7 progress on multi-step flows | met | 4-step flow, every item carries `Step N of 4` (`:7–10`), expressed as plain text per content-scope boundary. |
| T3 consistent marker semantics | met | No bold/italic/inline-code marks used at all (same as source); nothing to conflict. |
| C4 long pre-modifiers | n/a | English document. |
| X3 words without sentences | not hit | Every item and paragraph is a full sentence. |
| X6 table abuse | not hit | No tables. |
| X7 fold abuse | not hit | No folds; main path is fully visible. |
| X8 template padding | not hit | No section shells; nothing says "none" or "n/a" in the doc. |

Two honest gaps carry forward: **A1/A2/A7-partial** and **W5** cannot be satisfied without adding facts the source does not contain, and **S4** was a deliberate hold. Everything else the script cannot judge was reviewed and judged met; X-group deduction after is 0.

Verification passes on both scopes and the score moved 87.8 → 100.0. Here is the report.

## Done: `input.md` → `output.md`

**scope** `content` · **level** `deep` · written to `output.md`

The workspace is not a git repo, so the skill's default would be `input.adhd.md`; your instruction named `output.md`, so I wrote that and left `input.md` untouched (it is the verify baseline). `scope=content` → step 2 (`fmt`) was skipped by design.

**Script score 87.8 → 100.0 (+12.2)** — this is the script score only. 32 rules in this configuration need model judgment and the script counts them as "not hit"; it is not a final grade. My per-rule decisions are in the table below.

| Dimension | before | after | delta |
|---|---|---|---|
| First-screen conclusion (首屏结论力) | 40.0 | 100.0 | +60.0 |
| Chunking (分块粒度) | 92.0 | 100.0 | +8.0 |
| Scannability (扫读性) | 100.0 | 100.0 | 0 |
| Sentence load (句子负荷) | 100.0 | 100.0 | 0 |
| Actionability (行动性) | 100.0 | 100.0 | 0 |
| Typography (排版一致性) | 100.0 | 100.0 | 0 |
| Human feel (活人感) | 100.0 | 100.0 | 0 |

Anti-pattern deduction −0 → −0. Findings 2 → 0 (`H1` no first-screen conclusion, `P1` 4-sentence paragraph). M-group hits did not rise (0 → 0).

**verify** `--scope=content` **pass** (no hard failures, no warnings, no unknowns); `--scope=both` also pass. This covers the declared invariants only: code blocks, link targets, inline-code values, command options, paths, permission values, case-sensitive identifiers, and numeric/unit values are unchanged (no warnings raised). It is not a proof of semantic equivalence, and it says nothing about sentence-level meaning.

### What I changed
- Split the 4-sentence opening paragraph into a lead + a boundary paragraph (`output.md:3,5`); the lead is a new TL;DR sentence and the boundaries are the original sentences, verbatim.
- Lead line: "Retry a failed thumbnail job. The procedure has 4 steps, and one of them adds a 7-minute wait when the job's lock is active." — restates the source plus countable length (4 steps) and the source's own 7-minute wait. No total runtime invented.
- Step 1 split into two actions in-item: "Open the job panel. Select a failed job." (A8; no new list items — content scope).
- Step 2 branch split in-item: "If the job's lock is active, wait 7 minutes. When the wait is over, reload the panel once." The condition still controls both sub-actions, order kept, "once" kept, 7 kept.
- Step 4 gained the source's own success signal at the point of action: "Expected: status accepted." (A7 for that step).
- Progress labels `Step N of 4` in plain text inside the existing ordered items (N7; no headings, no checkboxes — content scope).

### Deliberately not changed
- **"Manual retry settings apply only to this browser session. Signing in elsewhere does not copy those manual settings."** — left verbatim. Rewriting risked generalizing "manual retry settings" to settings at large, or "browser session" to "device". This is the sharpest boundary in the file.
- **"Do not retry jobs marked archived."** — kept as a negative (W9's warning exception); kept as a plain sentence, not a `> **Warning**` blockquote, because that would be a layout change.
- **The closing pair of sentences** — verbatim. "Accepted" must not be flipped to "rendering is in progress"; the positive restatement "Expected: status accepted" sits in step 4 and the caveat stays where the source put it.
- **The H1** — `# Thumbnail recovery` unchanged, so **S4 is not met** (see table). Holding the title steady was a judgment call under "preserve the original layout style"; renaming is permitted by content scope but changes the runbook's identifier.
- **No expected output invented for steps 1–3**; no next step invented after step 4; no glosses for `job panel` / `job key` / `incident note` / `lock`. The source does not supply them, so those rules stay unmet rather than filled with fabricated UI behavior.
- **No new heading levels, no checkboxes, no `<details>`, no TOC, no tables, no bold/italic/code marks added.** Under `level=deep` the runbook skeleton would normally add step headings and checkboxes; `scope=content` forbids that and you asked to preserve the layout style, so the skeleton was applied only where it could be expressed as prose.

### Judge-rule decisions (32 rules)

Verdicts use the skill's four values: met（满足）/ not met（不满足）/ n/a（不适用）/ cannot judge（无法判断）. Locations are in `output.md` unless noted.

| Rule | Verdict | Basis |
|---|---|---|
| S4 title states the answer | **not met** | H1 kept as `# Thumbnail recovery` (topic-style). Deliberate: title is the doc's identifier and the layout was to be preserved. Optional alternative: `# Retry a failed thumbnail job`. |
| S5 conclusion first | met | Source's first sentence already was the conclusion; output keeps it first and sharpens it into the lead (`:3`). No block move, so no dangling reference. |
| S6 section order matches doc type | n/a | Runbook type, but the doc has no H2 sections and content scope forbids adding any; skeleton can't be applied without a layout change. |
| S8 section-opening sentence | n/a | No sections (single H1, paragraphs + one list). |
| H3 first screen says what you get | met | "Retry a failed thumbnail job." (`:3`) — reader payoff, not doc structure. |
| H4 time/length estimate | met | "has 4 steps, and one of them adds a 7-minute wait…" (`:3`). Length from the doc, duration from the source's own 7 minutes. No total invented. |
| P2 one topic per paragraph | met | `:3` what it does/how long · `:5` settings boundary + do-not-retry · `:11` success criteria. Original mixed 4 sentences into one paragraph. |
| P5 oversized quote block | n/a | No blockquotes. |
| L2 parallel clauses → list | n/a | No enumerable clause left; content scope also forbids changing list form. |
| L4 parallel list items | met | All four items open `Step N of 4 — ` + bare verb (Open/Select, wait/reload, Copy, Submit). |
| L7 items keep full meaning | met | Each item reads standalone; no keyword shrapnel (`:7–10`). |
| W2 active voice | met | All imperative/active; zero passive sentences. |
| W3 parenthetical asides | n/a | No parentheses. |
| W5 explain terms at first use | **not met** | `job panel`, `job key`, `incident note`, `lock` are undefined. Source gap — glossing them would mean inventing product behavior. |
| W7 you + present + concrete verbs | met | Imperatives carry second person; every verb is concrete and present tense. |
| W8 one clause per sentence | met | Longest sentence is a single-layer conditional (23 words); no nesting. |
| W9 negations → positive | met (exception held) | The two negations are warnings ("Do not retry jobs marked archived." `:5`; "Accepted does not mean the thumbnail has finished rendering." `:11`) and stay negative by rule. Flipping the second would assert something the source never says. |
| A1 next step at the end | **not met** | Doc ends on the success criterion, not a next action. The source never says what to do after submitting, so none was added. |
| A2 time estimate per step | **not met** (partly) | Only step 2 carries the source's 7 minutes; steps 1/3/4 have no basis and were not padded. |
| A3 default recommendation | n/a | No options to choose between; step 2 is a condition, not a choice. |
| A5 "do this one thing" | n/a | Deep-level rule aimed at long docs; this is a 12-line single-task runbook and the lead already carries the entry point. |
| A6 decision point gives its criterion | met | The only branch keeps its source criterion: "If the job's lock is active" (`:8`). |
| A7 expected output / verification | **not met** (1 of 4 steps) | Step 4 has the source's own signal at the action (`:10`), reinforced by `:11`. Steps 1–3 have no output, UI state, or check stated anywhere in the source — left unmet and reported rather than fabricated. |
| A8 one action per step | met | Step 1 → open / select; step 2 → wait / reload with the condition still governing both and the order intact; steps 3 and 4 were already single-action. Splitting done inside the existing items, no list items added. |
| N4 fold optional content | n/a | Nothing is off the main path; content scope forbids touching fold structure. |
| N7 progress on multi-step flows | met | 4-step flow, every item carries `Step N of 4` (`:7–10`), expressed as plain text per content-scope boundary. |
| T3 consistent marker semantics | met | No bold/italic/inline-code marks used at all (same as source); nothing to conflict. |
| C4 long pre-modifiers | n/a | English document. |
| X3 words without sentences | not hit | Every item and paragraph is a full sentence. |
| X6 table abuse | not hit | No tables. |
| X7 fold abuse | not hit | No folds; main path is fully visible. |
| X8 template padding | not hit | No section shells; nothing says "none" or "n/a" in the doc. |

Two honest gaps carry forward: **A1/A2/A7-partial** and **W5** cannot be satisfied without adding facts the source does not contain, and **S4** was a deliberate hold. Everything else the script cannot judge was reviewed and judged met; X-group deduction after is 0.
