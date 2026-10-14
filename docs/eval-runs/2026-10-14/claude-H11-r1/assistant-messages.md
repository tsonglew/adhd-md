I'll start by reading the skill snapshot and the input file.

Now I understand the audit mechanics. Let me check a couple of implementation details before writing the output.

The output is written and verified. Let me do a final check of the complete picture before reporting.

## Reformatted: `input.md` → `output.md`

**scope** `format` · **level** `standard` · written to **`output.md`** (input untouched; nothing was moved in place)

### Commands and exit status

| Command | Exit | Result |
|---|---|---|
| `audit input.md --level 2 --scope=format` | **0** | score 81.2, anti-pattern −8 |
| `audit output.md --level 2 --scope=format` | **0** | score 81.2, anti-pattern −8 |
| `verify input.md output.md --scope=format` | **0** | `status: pass` (0 hard failures, 0 warnings, 0 unknowns) — **not** `unknown` |
| `fmt output.md` | 0 | "格式已规范，无需修改" — no deterministic fixes pending |
| `report input.md output.md --scope=format` | **1** | score 81.2 → 81.2; exits 1 only because of its built-in "X must be 0 after" assertion (see below) |

### Script score (script score only — 23 rules are model-judged and counted as not-hit)

| Dimension | Weight | before | after |
|---|---|---|---|
| First-screen conclusion (hook) | 18% | 40.0 | 40.0 |
| Chunking | 18% | 100.0 | 100.0 |
| Scannability | 13% | 100.0 | 100.0 |
| Sentence load | 13% | 100.0 | 100.0 |
| Actionability | 12% | 100.0 | 100.0 |
| Typography | 13% | 100.0 | 100.0 |
| Human feel | 13% | 100.0 | 100.0 |
| **Total (after −8 X-deduction)** | | **81.2** | **81.2** |

### Anti-pattern deductions: −8 → −8 (X2, unchanged)

X2 has two triggers; the edit cleared one, the other cannot be cleared inside `scope=format`:

- **Cleared** — heading density was 5 headings / 20 lines = 1 per 4.0 lines (< 5). Now 5 / 30 = 1 per 6.0 lines. The three `N3` advisories ("add dividers between major sections") are also gone.
- **Remains** — "pure-prose sections average 22 units, below 25". Mechanism, verified by instrumenting the checker: the sections are title **0**, Outcome **26**, Decisions **37**, Rollback **23** units → 21.5. The title section counts 0 because heading text is excluded from section units and nothing non-heading sits between the H1 and the first H2. Total prose is fixed at 86 units, so *moving* any block up just relocates the 0 (average stays 21.5). Clearing it requires either ~14 new prose units (**content**) or deleting/merging a heading (**deletes content — forbidden by the iron rule**). Not zero, but no X points were *added* by this edit; the −8 was already in the source.

### Unjudged rules (script scored them as not-hit — this is **not** a pass)

All 23 judge rules at `standard` level: `S4 S5 H4 P2 P5 L2 L4 L7 W2 W3 W5 W8 A1 A7 A8 N4 N7 T3 C4 X3 X6 X7 X8`.

- **F-axis, in play for this run** (my judgment, not a script pass): `S5` — the answer block is already first, nothing needed moving. `P2` — satisfied better than before (one fact per bullet; rule and exception now separate paragraphs). `L2` — applied, wording reused verbatim. `T3` — bold used only for the two action owners. `N4/X7` — nothing folded. `X6` — no tables. `X8` — no template sub-headings. `P5` — no blockquotes.
- **C-axis, unreachable under `scope=format`**: `S4 H4 L4 L7 W2 W3 W5 W8 A1 A7 A8 N7 C4 X3`. Note `H4` (first-screen time/size estimate) is *required* at `standard` yet is a content-axis rule — writing "3 min read" would add words, so it stays unfulfilled by design.
- Hint-only rules: `N3` cleared by the dividers; `T5` no warning labels present; `L6` ≤7 items; `C6` Chinese-only.

### What I changed (all markup — zero words, numbers, units, conditions or exceptions touched)

- Outcome paragraph → 3-item bullet list, the three sentences reused character-for-character; the three parallel metrics now scan one per line (`L2`).
- Added `---` between the four H2 sections (the audit's own 3 `N3` advisories; `scope=format` allows dividers).
- Split the Rollback section's two sentences into two paragraphs at the existing sentence boundary — the rule and its exception ("A single slow query is not a rollback trigger.") now read separately.
- Bolded the two action owners (`**Alex**`, `**Search team**`) as field labels; no other emphasis added.

Verified preservation: `verify --scope=format` compares the full prose token multiset — zero missing, zero added tokens; all 8 numeric literals (100%, 210 ms, 250 ms, 680 ms, 600 ms, 0.5%, 1%, 10) and both conditions/exceptions intact. `pass` covers the declared invariants only; it is not a semantic-equivalence proof, and the 23 judge rules above remain unjudged rather than passed.

### What I deliberately did not change

- **The `H1` finding (hook 40/100) stays.** The conclusion *is* in the first 15 lines (`## Outcome`, line 3), so the rule's intent is met, but the checker only accepts a TL;DR before the first H2 or an H2 title containing a keyword (`tl;dr|summary|at a glance|…`). It is hidden from the `--scope=format` findings view (C axis) yet still scored. Clearing it needs a renamed heading or a new TL;DR line — **content**. I also declined the block-move workaround: lifting the Outcome bullets above their own heading leaves `## Outcome` empty, and this case says to preserve the ordering of information.
- **No heading removed or merged** to zero out X2 (that would delete content).
- **No TOC** — the doc is 30 lines (`N1` needs >80), and added link targets are a hard failure under `scope=format`.
- No emoji, tables, `<details>` folds, time estimates, or next-step annotations (content/last two are content-scope moves).

## Reformatted: `input.md` → `output.md`

**scope** `format` · **level** `standard` · written to **`output.md`** (input untouched; nothing was moved in place)

### Commands and exit status

| Command | Exit | Result |
|---|---|---|
| `audit input.md --level 2 --scope=format` | **0** | score 81.2, anti-pattern −8 |
| `audit output.md --level 2 --scope=format` | **0** | score 81.2, anti-pattern −8 |
| `verify input.md output.md --scope=format` | **0** | `status: pass` (0 hard failures, 0 warnings, 0 unknowns) — **not** `unknown` |
| `fmt output.md` | 0 | "格式已规范，无需修改" — no deterministic fixes pending |
| `report input.md output.md --scope=format` | **1** | score 81.2 → 81.2; exits 1 only because of its built-in "X must be 0 after" assertion (see below) |

### Script score (script score only — 23 rules are model-judged and counted as not-hit)

| Dimension | Weight | before | after |
|---|---|---|---|
| First-screen conclusion (hook) | 18% | 40.0 | 40.0 |
| Chunking | 18% | 100.0 | 100.0 |
| Scannability | 13% | 100.0 | 100.0 |
| Sentence load | 13% | 100.0 | 100.0 |
| Actionability | 12% | 100.0 | 100.0 |
| Typography | 13% | 100.0 | 100.0 |
| Human feel | 13% | 100.0 | 100.0 |
| **Total (after −8 X-deduction)** | | **81.2** | **81.2** |

### Anti-pattern deductions: −8 → −8 (X2, unchanged)

X2 has two triggers; the edit cleared one, the other cannot be cleared inside `scope=format`:

- **Cleared** — heading density was 5 headings / 20 lines = 1 per 4.0 lines (< 5). Now 5 / 30 = 1 per 6.0 lines. The three `N3` advisories ("add dividers between major sections") are also gone.
- **Remains** — "pure-prose sections average 22 units, below 25". Mechanism, verified by instrumenting the checker: the sections are title **0**, Outcome **26**, Decisions **37**, Rollback **23** units → 21.5. The title section counts 0 because heading text is excluded from section units and nothing non-heading sits between the H1 and the first H2. Total prose is fixed at 86 units, so *moving* any block up just relocates the 0 (average stays 21.5). Clearing it requires either ~14 new prose units (**content**) or deleting/merging a heading (**deletes content — forbidden by the iron rule**). Not zero, but no X points were *added* by this edit; the −8 was already in the source.

### Unjudged rules (script scored them as not-hit — this is **not** a pass)

All 23 judge rules at `standard` level: `S4 S5 H4 P2 P5 L2 L4 L7 W2 W3 W5 W8 A1 A7 A8 N4 N7 T3 C4 X3 X6 X7 X8`.

- **F-axis, in play for this run** (my judgment, not a script pass): `S5` — the answer block is already first, nothing needed moving. `P2` — satisfied better than before (one fact per bullet; rule and exception now separate paragraphs). `L2` — applied, wording reused verbatim. `T3` — bold used only for the two action owners. `N4/X7` — nothing folded. `X6` — no tables. `X8` — no template sub-headings. `P5` — no blockquotes.
- **C-axis, unreachable under `scope=format`**: `S4 H4 L4 L7 W2 W3 W5 W8 A1 A7 A8 N7 C4 X3`. Note `H4` (first-screen time/size estimate) is *required* at `standard` yet is a content-axis rule — writing "3 min read" would add words, so it stays unfulfilled by design.
- Hint-only rules: `N3` cleared by the dividers; `T5` no warning labels present; `L6` ≤7 items; `C6` Chinese-only.

### What I changed (all markup — zero words, numbers, units, conditions or exceptions touched)

- Outcome paragraph → 3-item bullet list, the three sentences reused character-for-character; the three parallel metrics now scan one per line (`L2`).
- Added `---` between the four H2 sections (the audit's own 3 `N3` advisories; `scope=format` allows dividers).
- Split the Rollback section's two sentences into two paragraphs at the existing sentence boundary — the rule and its exception ("A single slow query is not a rollback trigger.") now read separately.
- Bolded the two action owners (`**Alex**`, `**Search team**`) as field labels; no other emphasis added.

Verified preservation: `verify --scope=format` compares the full prose token multiset — zero missing, zero added tokens; all 8 numeric literals (100%, 210 ms, 250 ms, 680 ms, 600 ms, 0.5%, 1%, 10) and both conditions/exceptions intact. `pass` covers the declared invariants only; it is not a semantic-equivalence proof, and the 23 judge rules above remain unjudged rather than passed.

### What I deliberately did not change

- **The `H1` finding (hook 40/100) stays.** The conclusion *is* in the first 15 lines (`## Outcome`, line 3), so the rule's intent is met, but the checker only accepts a TL;DR before the first H2 or an H2 title containing a keyword (`tl;dr|summary|at a glance|…`). It is hidden from the `--scope=format` findings view (C axis) yet still scored. Clearing it needs a renamed heading or a new TL;DR line — **content**. I also declined the block-move workaround: lifting the Outcome bullets above their own heading leaves `## Outcome` empty, and this case says to preserve the ordering of information.
- **No heading removed or merged** to zero out X2 (that would delete content).
- **No TOC** — the doc is 30 lines (`N1` needs >80), and added link targets are a hard failure under `scope=format`.
- No emoji, tables, `<details>` folds, time estimates, or next-step annotations (content/last two are content-scope moves).
