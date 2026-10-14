I'll start by reading the skill and the input file.

Now I'll write the reformatted output — format-only changes, no wording touched.

Done. `output.md` written; `input.md` untouched (891 bytes, original mtime — I never opened it for writing).

## Result: `input.md` → `output.md`

**scope** `format` · **level** `standard` · target `output.md` (case instruction; the skill's own rule for a non-git dir would have been `input.md.adhd.md`, so either way the input is not overwritten)

**Script score (script-computed only, not a final score): 100.0 → 100.0 (+0.0)**

| Dimension | before | after |
|---|---|---|
| 首屏结论力 hook | 100.0 | 100.0 |
| 分块粒度 chunk | 100.0 | 100.0 |
| 扫读性 scan | 100.0 | 100.0 |
| 句子负荷 sentence | 100.0 | 100.0 |
| 行动性 action | 100.0 | 100.0 |
| 排版一致性 typo | 100.0 | 100.0 |
| 活人感 human | 100.0 | 100.0 |

**Exit statuses**
- `audit output.md --level 2 --scope=format` → **exit 0**, score 100.0, findings 0 (advisory 0). Same for the before-run on `input.md` (exit 0, 100.0).
- `verify input.md output.md --scope=format` → **exit 0**, `status: pass`, `hard_failures: []`, `warnings: []`, `unknowns: []`, `ok: true`. This is a real `pass`; nothing was reported as pass on the strength of an `unknown`.
- `fmt input.md` → "格式已规范，无需修改" (no deterministic fixes were pending).

**Anti-pattern deductions (X group): −0 → −0** — `x_deduct: 0`, `x_hits: {}`. No X1–X8 hit, before or after. The after value is 0, as required.

**Unjudged rules — these were NOT scored and I am not reporting them as passed**
- In `scope=format` at `level=2`: **9 judge-only rules** — `S5, P2, P5, L2, N4, T3, X6, X7, X8`, plus **4 hint-only** (`L6, N3, T5, C6`) which carry no score, **2 auto-fix-only** (`P3, T6`) and the **X4 hard gate**. Coverage line: applicable 39 · script-checked 23 (all 23 scored) · hint 4 · judge 9 · format-only 2 · hard gate 1 · unimplemented 0.
- Script-wide (all axes, not scope-filtered) **23 rules still need model judgment**: `S4, S5, H4, P2, P5, L2, L4, L7, W2, W3, W5, W8, A1, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8`. The auditor counts them as unmatched, so 100.0 is a floor, not a verdict.
- My manual read of the 9 in-scope ones (reported as judgment, not as script results): P2 satisfied by the paragraph split below; L2 has no legal instance (the only parallel pair, "the service hostname or client trust bundle", would lose the word "or"); S5 has no conclusion block to hoist, and the case instructions require preserving information order; N4/X7 — nothing off the main path, so nothing was folded; T3 — no emphasis markers were added at all; X3/X6/X8 — no list items were clipped, no tables and no template headings were introduced.

**What I changed** (two moves, both markup/reflow only — token multiset *and* token order are byte-identical to the input; the only new character in the file is `>`)
1. Split the prerequisite block at its existing sentence boundary, so the "Do not remove the current certificate during the check." constraint stands on its own line instead of hiding behind the access prerequisite (P2: one topic per paragraph; P1 sentence/word caps unaffected).
2. Set the `495` failure branch as a blockquote, so the stop-the-rollout condition reads as a callout off the main path. I did **not** write `> **Warning**:` — T5's canonical label needs a word that does not exist in the original, and adding words is content scope.

**Deliberately not changed**
- No TL;DR, no time estimate, no "Step X of N" progress labels, no rewritten headings, no "what you'll be able to do" line — all of these are `content`-axis rules (H1/H2/H4/A2/N7) and would be hard failures under `format`.
- No bold anywhere. The doc has no term that earns an anchor, and per T3 bold means key term; the bold budget (≤8%) is unused rather than spent on noise.
- No TOC — N1 only requires one past 80 lines; this file is 16.
- No `<details>` folding — the six steps are the main path (folding them would be X7).
- No checklist conversion — L3 keeps procedures as ordered lists; `- [ ]` is for trackable items, and these steps are sequential.
- Blocks not reordered. There is no conclusion block to hoist (S5), and the case requires preserving the ordering of information; the closing "does not change the service hostname or client trust bundle" note stays where it is.
- Wording, numbers, units, conditions and exceptions untouched: `48 hours`, `/health`, `200`, `495`, `<name>`-free of new content, and the input's single trailing newline preserved.

So the honest summary of this case: the input was already format-clean (audit had zero findings before I started), and under `scope=format` the ceiling is exactly this — structure can move, words cannot. Anything more visible would have required `content` scope.

Done. `output.md` written; `input.md` untouched (891 bytes, original mtime — I never opened it for writing).

## Result: `input.md` → `output.md`

**scope** `format` · **level** `standard` · target `output.md` (case instruction; the skill's own rule for a non-git dir would have been `input.md.adhd.md`, so either way the input is not overwritten)

**Script score (script-computed only, not a final score): 100.0 → 100.0 (+0.0)**

| Dimension | before | after |
|---|---|---|
| 首屏结论力 hook | 100.0 | 100.0 |
| 分块粒度 chunk | 100.0 | 100.0 |
| 扫读性 scan | 100.0 | 100.0 |
| 句子负荷 sentence | 100.0 | 100.0 |
| 行动性 action | 100.0 | 100.0 |
| 排版一致性 typo | 100.0 | 100.0 |
| 活人感 human | 100.0 | 100.0 |

**Exit statuses**
- `audit output.md --level 2 --scope=format` → **exit 0**, score 100.0, findings 0 (advisory 0). Same for the before-run on `input.md` (exit 0, 100.0).
- `verify input.md output.md --scope=format` → **exit 0**, `status: pass`, `hard_failures: []`, `warnings: []`, `unknowns: []`, `ok: true`. This is a real `pass`; nothing was reported as pass on the strength of an `unknown`.
- `fmt input.md` → "格式已规范，无需修改" (no deterministic fixes were pending).

**Anti-pattern deductions (X group): −0 → −0** — `x_deduct: 0`, `x_hits: {}`. No X1–X8 hit, before or after. The after value is 0, as required.

**Unjudged rules — these were NOT scored and I am not reporting them as passed**
- In `scope=format` at `level=2`: **9 judge-only rules** — `S5, P2, P5, L2, N4, T3, X6, X7, X8`, plus **4 hint-only** (`L6, N3, T5, C6`) which carry no score, **2 auto-fix-only** (`P3, T6`) and the **X4 hard gate**. Coverage line: applicable 39 · script-checked 23 (all 23 scored) · hint 4 · judge 9 · format-only 2 · hard gate 1 · unimplemented 0.
- Script-wide (all axes, not scope-filtered) **23 rules still need model judgment**: `S4, S5, H4, P2, P5, L2, L4, L7, W2, W3, W5, W8, A1, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8`. The auditor counts them as unmatched, so 100.0 is a floor, not a verdict.
- My manual read of the 9 in-scope ones (reported as judgment, not as script results): P2 satisfied by the paragraph split below; L2 has no legal instance (the only parallel pair, "the service hostname or client trust bundle", would lose the word "or"); S5 has no conclusion block to hoist, and the case instructions require preserving information order; N4/X7 — nothing off the main path, so nothing was folded; T3 — no emphasis markers were added at all; X3/X6/X8 — no list items were clipped, no tables and no template headings were introduced.

**What I changed** (two moves, both markup/reflow only — token multiset *and* token order are byte-identical to the input; the only new character in the file is `>`)
1. Split the prerequisite block at its existing sentence boundary, so the "Do not remove the current certificate during the check." constraint stands on its own line instead of hiding behind the access prerequisite (P2: one topic per paragraph; P1 sentence/word caps unaffected).
2. Set the `495` failure branch as a blockquote, so the stop-the-rollout condition reads as a callout off the main path. I did **not** write `> **Warning**:` — T5's canonical label needs a word that does not exist in the original, and adding words is content scope.

**Deliberately not changed**
- No TL;DR, no time estimate, no "Step X of N" progress labels, no rewritten headings, no "what you'll be able to do" line — all of these are `content`-axis rules (H1/H2/H4/A2/N7) and would be hard failures under `format`.
- No bold anywhere. The doc has no term that earns an anchor, and per T3 bold means key term; the bold budget (≤8%) is unused rather than spent on noise.
- No TOC — N1 only requires one past 80 lines; this file is 16.
- No `<details>` folding — the six steps are the main path (folding them would be X7).
- No checklist conversion — L3 keeps procedures as ordered lists; `- [ ]` is for trackable items, and these steps are sequential.
- Blocks not reordered. There is no conclusion block to hoist (S5), and the case requires preserving the ordering of information; the closing "does not change the service hostname or client trust bundle" note stays where it is.
- Wording, numbers, units, conditions and exceptions untouched: `48 hours`, `/health`, `200`, `495`, `<name>`-free of new content, and the input's single trailing newline preserved.

So the honest summary of this case: the input was already format-clean (audit had zero findings before I started), and under `scope=format` the ceiling is exactly this — structure can move, words cannot. Anything more visible would have required `content` scope.
