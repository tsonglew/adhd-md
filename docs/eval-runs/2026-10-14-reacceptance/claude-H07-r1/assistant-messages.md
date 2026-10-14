I'll start by reading the skill definition and the input file.

Now let me read the required reference files and check the script directory.

Let me examine the M-group and X-group detection patterns to make sure my rewrite won't trip them.

Now I'll write the rewritten version. Key constraints I'm holding: `scope=content` (wording only — no new heading levels, no list-form changes), all numbers/units/conditions preserved, no invented product behavior, and no M-group patterns.

Both checks pass. Let me run the boundary check the skill requires — verifying every fact, condition, and numeric edge is present in the output — plus sentence-level metrics.

The doc is 136 words, so let me correct the reading-time estimate to stay accurate.

All gates pass. Here's the final report.

## Done: `output.md`

**scope** `content` · **level** `standard` (level 2) · doc type README · language `en`
Written to `output.md` — `input.md` untouched. (Workspace is not a git repo, so the in-place rule in step 0 doesn't apply; the case explicitly asked for a separate output file.)

**Script score 100.0 → 100.0 (+0.0)** — this is the *script* score, not a final score: `score.band` is `null`, and 23 judge rules are counted as **unjudged**, not as passes.

| Dimension | before | after | delta |
|---|---|---|---|
| 首屏结论力 hook | 100.0 | 100.0 | +0.0 |
| 分块粒度 chunk | 100.0 | 100.0 | +0.0 |
| 扫读性 scan | 100.0 | 100.0 | +0.0 |
| 句子负荷 sentence | 100.0 | 100.0 | +0.0 |
| 行动性 action | 100.0 | 100.0 | +0.0 |
| 排版一致性 typo | 100.0 | 100.0 | +0.0 |
| 活人感 human | 100.0 | 100.0 | +0.0 |

**Anti-pattern deductions (X group): −0 → −0** — `x_hits` is empty for both files: no X1 emoji, X2 fragmentation, X5 bold overflow; X3/X6/X7/X8 not hit (no keyword-only list items, no tables, no `<details>`, no template padding). X4 (information loss) is a hard gate and is cleared by `verify`.

**verify(content) → `pass`** (`status: pass`, `ok: true`; 0 hard failures, 0 warnings, 0 unknowns; exit 0). Not `unknown`, and not reported as anything else. Scope of that pass: code blocks, link targets, inline literals, protected identifiers, numeric literals + repeat counts. It does **not** prove semantic equivalence — sentence-level meaning and the judge rules below are human/model calls.

**Unjudged rules (23):** S4, S5, H4, P2, P5, L2, L4, L7, W2, W3, W5, W8, A1, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8. My per-rule calls:

| Rule | Verdict | Basis |
|---|---|---|
| S4 headings state the answer | met | `## Download an export in 4 steps`; `## Limits: 2 GB splits, 30-minute links, owners only` |
| S5 conclusion first | met (no move) | Source already led with the conclusion; block moves are a *format* action, out of scope for `content` |
| H4 time/length estimate | met | `Reading time: about 1 minute.` (line 5, first screen; page is ~136 words of prose) |
| P2 one topic per paragraph | met | contents/audience · read time · recycle-bin relation |
| P5 long quote blocks | n/a | no blockquotes |
| L2 clauses → list | n/a (scope) | format action; `content` must not change list form |
| L4 parallel list items | met (note) | bullets 1–3 open subject + present tense; bullet 4 stays a conditional directive because it is a recovery step, not a limit — same shape as the source |
| L7 list items keep meaning | met | every bullet is a full sentence; nothing cut to keywords |
| W2 active voice ≤10% | met | 0 passives: "are split" → "The archive splits…", "after it is created" → "after creation" |
| W3 parenthetical insertions | n/a | none used |
| W5 explain terms at first use | met | only abbreviation is ZIP (standard format name); no jargon introduced |
| W8 one clause per sentence | met | longest sentence 17 words, one relative clause |
| A1 section ends with a next step | met | Download ends on the last action; Limits ends on the empty-archive directive |
| **A7 expected output / verification** | **not met (source gap)** | Steps 2 and 3 carry source-based checks (which exports *are not* listed; date + row count). Steps 1 and 4 have no documented output or success criterion anywhere in the source — inventing UI behaviour is forbidden, so the gap is preserved and reported, not filled |
| **A8 one action per step** | **not met (scope limit)** | Step 3 still holds two actions (check → download) in one numbered item; `content` forbids adding list items, and per `rules.md` in-item sentence splitting would not change the verdict — the original "before you download" prerequisite is kept intact |
| N7 progress on ≥4 steps | met | 4-step flow labelled `in 4 steps` in the H2; items keep real numbers 1–4 for re-entry; `content` forbids per-step headings |
| T3 marker semantics | met | the source's single bold span (a UI path) preserved as-is; no new bold added |
| C4 Chinese long modifiers | n/a | English document |
| X3 / X6 / X7 / X8 | not hit | complete-sentence items; no tables; no folding; no repeated empty sub-headings |

**What I changed**
- Heading text → answer-bearing: `Download an export` → `Download an export in 4 steps`; `Limits` → `Limits: 2 GB splits, 30-minute links, owners only` (content)
- Two passives made active: `are split` → `The archive splits…`; `after it is created` → `after creation` (content, W2)
- One new line at first screen: `Reading time: about 1 minute.` (content, H4)
- One new sentence in step 2: "Exports that failed before upload, or that are older than 14 days, do not appear in the list." — a restatement of the two exclusion rules already in the source, used as the step's check (A7), no new facts
- Second-person tightening: `before downloading` → `before you download`; `before requesting` → `before you request`; `It is available only to workspace owners` → `Only workspace owners can view it`

**What I deliberately did not change**
- `**Workspace settings → Exports**` — the source's only emphasis marker, preserved verbatim (content scope must keep emphasis markers)
- Step 3's compound wording and step/list structure — order, list forms and step count identical; splitting the action is not a fix for A8 under this scope
- The recycle-bin paragraph and step 4 as-is — already active and single-topic
- The `N3` advisory finding (no divider between the two H2 sections) — present before *and* after (全文 findings 1 → 1); adding `---` is a layout change outside `scope=content`
- No invented UI details, thresholds, or outputs (e.g. step 3's "row count" stays unquantified; no claim about what the Exports screen shows)

**Facts verified preserved:** 14 days · 2 GB · 30 minutes · ZIP (3 occurrences in both files) · owners-only access · excludes pre-upload failures · separate from recycle bin · deleting export ≠ deleting source records · `approved project folder` · "may contain customer data" · guests cannot view · empty archive → check selected workspace **before** requesting a new export. All 16 boundary checks pass.

All gates pass. Here's the final report.

## Done: `output.md`

**scope** `content` · **level** `standard` (level 2) · doc type README · language `en`
Written to `output.md` — `input.md` untouched. (Workspace is not a git repo, so the in-place rule in step 0 doesn't apply; the case explicitly asked for a separate output file.)

**Script score 100.0 → 100.0 (+0.0)** — this is the *script* score, not a final score: `score.band` is `null`, and 23 judge rules are counted as **unjudged**, not as passes.

| Dimension | before | after | delta |
|---|---|---|---|
| 首屏结论力 hook | 100.0 | 100.0 | +0.0 |
| 分块粒度 chunk | 100.0 | 100.0 | +0.0 |
| 扫读性 scan | 100.0 | 100.0 | +0.0 |
| 句子负荷 sentence | 100.0 | 100.0 | +0.0 |
| 行动性 action | 100.0 | 100.0 | +0.0 |
| 排版一致性 typo | 100.0 | 100.0 | +0.0 |
| 活人感 human | 100.0 | 100.0 | +0.0 |

**Anti-pattern deductions (X group): −0 → −0** — `x_hits` is empty for both files: no X1 emoji, X2 fragmentation, X5 bold overflow; X3/X6/X7/X8 not hit (no keyword-only list items, no tables, no `<details>`, no template padding). X4 (information loss) is a hard gate and is cleared by `verify`.

**verify(content) → `pass`** (`status: pass`, `ok: true`; 0 hard failures, 0 warnings, 0 unknowns; exit 0). Not `unknown`, and not reported as anything else. Scope of that pass: code blocks, link targets, inline literals, protected identifiers, numeric literals + repeat counts. It does **not** prove semantic equivalence — sentence-level meaning and the judge rules below are human/model calls.

**Unjudged rules (23):** S4, S5, H4, P2, P5, L2, L4, L7, W2, W3, W5, W8, A1, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8. My per-rule calls:

| Rule | Verdict | Basis |
|---|---|---|
| S4 headings state the answer | met | `## Download an export in 4 steps`; `## Limits: 2 GB splits, 30-minute links, owners only` |
| S5 conclusion first | met (no move) | Source already led with the conclusion; block moves are a *format* action, out of scope for `content` |
| H4 time/length estimate | met | `Reading time: about 1 minute.` (line 5, first screen; page is ~136 words of prose) |
| P2 one topic per paragraph | met | contents/audience · read time · recycle-bin relation |
| P5 long quote blocks | n/a | no blockquotes |
| L2 clauses → list | n/a (scope) | format action; `content` must not change list form |
| L4 parallel list items | met (note) | bullets 1–3 open subject + present tense; bullet 4 stays a conditional directive because it is a recovery step, not a limit — same shape as the source |
| L7 list items keep meaning | met | every bullet is a full sentence; nothing cut to keywords |
| W2 active voice ≤10% | met | 0 passives: "are split" → "The archive splits…", "after it is created" → "after creation" |
| W3 parenthetical insertions | n/a | none used |
| W5 explain terms at first use | met | only abbreviation is ZIP (standard format name); no jargon introduced |
| W8 one clause per sentence | met | longest sentence 17 words, one relative clause |
| A1 section ends with a next step | met | Download ends on the last action; Limits ends on the empty-archive directive |
| **A7 expected output / verification** | **not met (source gap)** | Steps 2 and 3 carry source-based checks (which exports *are not* listed; date + row count). Steps 1 and 4 have no documented output or success criterion anywhere in the source — inventing UI behaviour is forbidden, so the gap is preserved and reported, not filled |
| **A8 one action per step** | **not met (scope limit)** | Step 3 still holds two actions (check → download) in one numbered item; `content` forbids adding list items, and per `rules.md` in-item sentence splitting would not change the verdict — the original "before you download" prerequisite is kept intact |
| N7 progress on ≥4 steps | met | 4-step flow labelled `in 4 steps` in the H2; items keep real numbers 1–4 for re-entry; `content` forbids per-step headings |
| T3 marker semantics | met | the source's single bold span (a UI path) preserved as-is; no new bold added |
| C4 Chinese long modifiers | n/a | English document |
| X3 / X6 / X7 / X8 | not hit | complete-sentence items; no tables; no folding; no repeated empty sub-headings |

**What I changed**
- Heading text → answer-bearing: `Download an export` → `Download an export in 4 steps`; `Limits` → `Limits: 2 GB splits, 30-minute links, owners only` (content)
- Two passives made active: `are split` → `The archive splits…`; `after it is created` → `after creation` (content, W2)
- One new line at first screen: `Reading time: about 1 minute.` (content, H4)
- One new sentence in step 2: "Exports that failed before upload, or that are older than 14 days, do not appear in the list." — a restatement of the two exclusion rules already in the source, used as the step's check (A7), no new facts
- Second-person tightening: `before downloading` → `before you download`; `before requesting` → `before you request`; `It is available only to workspace owners` → `Only workspace owners can view it`

**What I deliberately did not change**
- `**Workspace settings → Exports**` — the source's only emphasis marker, preserved verbatim (content scope must keep emphasis markers)
- Step 3's compound wording and step/list structure — order, list forms and step count identical; splitting the action is not a fix for A8 under this scope
- The recycle-bin paragraph and step 4 as-is — already active and single-topic
- The `N3` advisory finding (no divider between the two H2 sections) — present before *and* after (全文 findings 1 → 1); adding `---` is a layout change outside `scope=content`
- No invented UI details, thresholds, or outputs (e.g. step 3's "row count" stays unquantified; no claim about what the Exports screen shows)

**Facts verified preserved:** 14 days · 2 GB · 30 minutes · ZIP (3 occurrences in both files) · owners-only access · excludes pre-upload failures · separate from recycle bin · deleting export ≠ deleting source records · `approved project folder` · "may contain customer data" · guests cannot view · empty archive → check selected workspace **before** requesting a new export. All 16 boundary checks pass.
