I'll start by reading the skill definition and the input file.

Now I have a clear picture. Let me write the rewritten version.

Final state verified. Here's the report.

## Rewritten: `input.md` → `output.md`

**scope** `content` · **level** `standard` · English README · written to `output.md` (input left untouched; the skill's default `<name>.adhd.md` naming is overridden by your explicit output path)

### Script score

**100.0 → 100.0 (+0.0)** — this is the script score only, not a final score.

| Dimension | before | after | delta |
|---|---|---|---|
| First-screen conclusion (18%) | 100.0 | 100.0 | +0.0 |
| Chunk granularity (18%) | 100.0 | 100.0 | +0.0 |
| Scannability (13%) | 100.0 | 100.0 | +0.0 |
| Sentence load (13%) | 100.0 | 100.0 | +0.0 |
| Actionability (12%) | 100.0 | 100.0 | +0.0 |
| Typography consistency (13%) | 100.0 | 100.0 | +0.0 |
| Human feel (13%) | 100.0 | 100.0 | +0.0 |

**Anti-pattern deductions (X group): −0 → −0** — X1–X8 no hits after. Bold density unchanged (one run), no emoji, no tables, no folding, no new headings.

### Verify status

- **`verify --scope=content` → pass** (status `pass`, exit 0; `hard_failures: []`, `warnings: []`, `unknowns: []`). Not `unknown` — but `pass` only covers the declared machine checks (values and repeat-counts of numbers/units, link targets, code blocks, inline code, CLI flags, paths, identifiers). It is not a proof of semantic equivalence; wording-level meaning was reviewed by hand.
- For reference: `verify --scope=format` reports hard failures on prose-token changes. That is expected — words were changed by design under `content` scope; the format gate only binds when `scope=format`.

### Unjudged rules (script did not score these — not a pass)

23 rules: S4, S5, H4, P2, P5, L2, L4, L7, W2, W3, W5, W8, A1, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8.
Within `standard` + `content`, 14 are judge-only: S4, H4, L4, L7, W2, W3, W5, W8, A1, A7, A8, N7, C4, X3. I addressed S4, H4, W2, A7, N7 by hand and left the rest deliberately (below).

### What I changed (all content axis)

- Added the length estimate on the first screen: `Reading time: about 1 minute.` (H4).
- Made both H2s state the answer, not the topic: `## Download an export in 4 steps` · `## Limits: 2 GB, 30 minutes, no guest access` (S4). "4 steps" is a count of the original's own numbered steps, not a new fact.
- Passive → active/second person: `It is available only to workspace owners` → `Only workspace owners can access it`; `after it is created` → `after you create it` (W2).
- Gave each step its check/expectation (A7): step 1 lands on the exports list; step 2 shows only completed exports; step 3's date and row count tell you which export you get; step 4's reason (customer data) backs the approved-folder rule. Every added sentence reuses facts already in the original — no invented outputs or UI behavior.
- Split run-on tails: `before downloading` → `before you download`, `before requesting` → `before you request`.

Preserved verbatim: 14 days, 2 GB, 30 minutes, `**Workspace settings → Exports**`, ZIP file, date and row count, approved project folder, recycle bin, source records, "only workspace owners", "does not include files that failed before upload", "if the archive is empty". No code blocks or link targets existed in the source.

### What I deliberately did not change

- **No TL;DR list.** The lead paragraph already is the conclusion; a 5-item recap would only repeat it (X2/X8 risk).
- **No `---` dividers** between the two H2s — N3 is an F-axis advisory, out of scope for `content`.
- **List form, paragraph boundaries, and collapse structure untouched** — numbered list stays 4 items, bullets stay 4, no `<details>` (format axis).
- **No per-step "Step X of 4" labels.** The steps already carry real numbers 1–4 and the total is in the heading, which is what N7 is for (re-locating after losing focus); repeating it on four one-line steps is noise.
- **H1 kept as `Local export archive`** — S4 targets section headings, not the document title.
- **`A link` stays indefinite** — the original never says which link, so I did not write "the download link".
- **`Exports larger than 2 GB are split...` stays passive** — making it active would require inventing an actor. One passive in ~16 sentences (~6%) is inside W2's 10% budget.
- **W5 (term explanation) not applied** — the doc has no acronyms; the domain nouns (export, workspace, recycle bin) are used self-evidently, and glossing them would mean inventing definitions.

Final state verified. Here's the report.

## Rewritten: `input.md` → `output.md`

**scope** `content` · **level** `standard` · English README · written to `output.md` (input left untouched; the skill's default `<name>.adhd.md` naming is overridden by your explicit output path)

### Script score

**100.0 → 100.0 (+0.0)** — this is the script score only, not a final score.

| Dimension | before | after | delta |
|---|---|---|---|
| First-screen conclusion (18%) | 100.0 | 100.0 | +0.0 |
| Chunk granularity (18%) | 100.0 | 100.0 | +0.0 |
| Scannability (13%) | 100.0 | 100.0 | +0.0 |
| Sentence load (13%) | 100.0 | 100.0 | +0.0 |
| Actionability (12%) | 100.0 | 100.0 | +0.0 |
| Typography consistency (13%) | 100.0 | 100.0 | +0.0 |
| Human feel (13%) | 100.0 | 100.0 | +0.0 |

**Anti-pattern deductions (X group): −0 → −0** — X1–X8 no hits after. Bold density unchanged (one run), no emoji, no tables, no folding, no new headings.

### Verify status

- **`verify --scope=content` → pass** (status `pass`, exit 0; `hard_failures: []`, `warnings: []`, `unknowns: []`). Not `unknown` — but `pass` only covers the declared machine checks (values and repeat-counts of numbers/units, link targets, code blocks, inline code, CLI flags, paths, identifiers). It is not a proof of semantic equivalence; wording-level meaning was reviewed by hand.
- For reference: `verify --scope=format` reports hard failures on prose-token changes. That is expected — words were changed by design under `content` scope; the format gate only binds when `scope=format`.

### Unjudged rules (script did not score these — not a pass)

23 rules: S4, S5, H4, P2, P5, L2, L4, L7, W2, W3, W5, W8, A1, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8.
Within `standard` + `content`, 14 are judge-only: S4, H4, L4, L7, W2, W3, W5, W8, A1, A7, A8, N7, C4, X3. I addressed S4, H4, W2, A7, N7 by hand and left the rest deliberately (below).

### What I changed (all content axis)

- Added the length estimate on the first screen: `Reading time: about 1 minute.` (H4).
- Made both H2s state the answer, not the topic: `## Download an export in 4 steps` · `## Limits: 2 GB, 30 minutes, no guest access` (S4). "4 steps" is a count of the original's own numbered steps, not a new fact.
- Passive → active/second person: `It is available only to workspace owners` → `Only workspace owners can access it`; `after it is created` → `after you create it` (W2).
- Gave each step its check/expectation (A7): step 1 lands on the exports list; step 2 shows only completed exports; step 3's date and row count tell you which export you get; step 4's reason (customer data) backs the approved-folder rule. Every added sentence reuses facts already in the original — no invented outputs or UI behavior.
- Split run-on tails: `before downloading` → `before you download`, `before requesting` → `before you request`.

Preserved verbatim: 14 days, 2 GB, 30 minutes, `**Workspace settings → Exports**`, ZIP file, date and row count, approved project folder, recycle bin, source records, "only workspace owners", "does not include files that failed before upload", "if the archive is empty". No code blocks or link targets existed in the source.

### What I deliberately did not change

- **No TL;DR list.** The lead paragraph already is the conclusion; a 5-item recap would only repeat it (X2/X8 risk).
- **No `---` dividers** between the two H2s — N3 is an F-axis advisory, out of scope for `content`.
- **List form, paragraph boundaries, and collapse structure untouched** — numbered list stays 4 items, bullets stay 4, no `<details>` (format axis).
- **No per-step "Step X of 4" labels.** The steps already carry real numbers 1–4 and the total is in the heading, which is what N7 is for (re-locating after losing focus); repeating it on four one-line steps is noise.
- **H1 kept as `Local export archive`** — S4 targets section headings, not the document title.
- **`A link` stays indefinite** — the original never says which link, so I did not write "the download link".
- **`Exports larger than 2 GB are split...` stays passive** — making it active would require inventing an actor. One passive in ~16 sentences (~6%) is inside W2's 10% budget.
- **W5 (term explanation) not applied** — the doc has no acronyms; the domain nouns (export, workspace, recycle bin) are used self-evidently, and glossing them would mean inventing definitions.
