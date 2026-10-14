I'll start by reading the skill definition and the input file.

Deterministic layer is already clean and script score is 100. Let me look at the scoring internals briefly, then make the format-axis edits.

Deterministic layer is clean. Now the format-axis restructuring (paragraph splits at existing sentence boundaries, one parallel clause → list, all original wording reused).

One refinement: full-sentence list items should keep terminal punctuation, which also preserves the original sentence-ending `.`.

Done. Report below.

## Completed: `output.md`

**scope** `format` · **level** `deep` · written to `output.md` — `input.md` untouched (no git repo here, so I did not write in place)

### Command results

| Command | Exit | Result |
|---|---|---|
| `audit input.md --scope=format --level 3` | `0` | 100.0 |
| `audit output.md --scope=format --level 3` | `0` | 100.0 |
| `verify input.md output.md --scope=format` | `0` | `status: pass` |
| `fmt output.md --check` | `0` | already canonical, no changes needed |
| `report input.md output.md --scope=format --level 3` | `0` | verify(format) 通过 |

`verify` JSON: `status: "pass"`, `hard_failures: []`, `warnings: []`, `unknowns: []`, `ok: true`. **No `unknown` anywhere — nothing here is an unknown being dressed up as a pass.** Note what `pass` covers: the declared machine checks only (protected values, code fences, block mapping). It is not a proof of semantic equivalence.

### Script score 100.0 → 100.0 (+0.0)

| Dimension | Weight | Before | After |
|---|---|---|---|
| Hook / 首屏结论力 | 18% | 100.0 | 100.0 |
| Chunking / 分块粒度 | 18% | 100.0 | 100.0 |
| Scanability / 扫读性 | 13% | 100.0 | 100.0 |
| Sentence load / 句子负荷 | 13% | 100.0 | 100.0 |
| Actionability / 行动性 | 12% | 100.0 | 100.0 |
| Typography / 排版一致性 | 13% | 100.0 | 100.0 |
| Human feel / 活人感 | 13% | 100.0 | 100.0 |

The input was already clean on every deterministic axis, so this is a script score, not a final score.

**Anti-pattern deductions (X group): −0 → −0** (`x_hits: {}`). No X1 emoji, X2 fragmentation, X5 over-bolding, etc.

**Unjudged rules — not passes.** The score line reports **32 rules needing model judgment**, counted as not-hit and unscored: S4, S5, S6, S8, H3, H4, P2, P5, L2, L4, L7, W2, W3, W5, W7, W8, W9, A1, A2, A3, A5, A6, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8. Rule coverage at deep·format: **41 applicable** — 23 script-checked (scored), 5 hint-only (S7, L6, N3, T5, C6 — no points either way), 10 judge-only on the F axis (S5, S6, P2, P5, L2, N4, T3, X6, X7, X8), 2 auto-fix-only (P3, T6), 1 hard gate (X4, passed via verify).

### What changed

- **Split the 3-sentence note paragraph into two** — the auth-error exception (`401`/`403` never retried) now stands as its own block instead of hiding as sentence 3 of 3. Split at an existing sentence boundary; zero words touched.
- **Split the closing 2-sentence paragraph** — the restart requirement and the unit notes are now separate blocks.
- **Semicolon-joined parallel clause → 2-item list** — `` `visibilitySeconds` is measured in seconds; `backoffMs` is measured in milliseconds. `` becomes two bullets, original wording reused verbatim.

Character-level accounting: **all 99 words identical and in identical order**; the only punctuation delta is the `;` at the clause break, which became `.` when the clause became a list item. Inline code values, numbers/ranges (`45`, `5–600`, `1–8`, `100–5000`, `401`, `403`), units, identifiers, the `yaml` fence tag, and the code-block body are byte-identical.

### Deliberately not changed

- **No block reordering.** The restart caveat at the end is arguably the loudest candidate for S5 hoisting, but the task requires preserving the ordering of information, and `deep` skeleton guidance for reference docs says the quick-reference table stays first and stable. Moving the caveat above the table would break lookup-by-scan and risk dangling references.
- **No TL;DR, time estimate, next-step line, or "what you'll be able to do" (H1/H2/H3/H4, A1/A2/A5).** All require writing new text — that is the `content` axis. They remain unjudged, not satisfied.
- **No new headings.** "Notes" / "Example" would be new words (S8, S6 partly unreachable under `format`).
- **No bolding or `> **注意**` labels.** The source has no bold and no warning labels; adding them means new characters, and emphasis-vs-key-term (T3) is the wrong trade for a parameter reference.
- **`<details>` folding skipped.** The YAML example and both notes are main-path content — folding them would be X7 abuse (N4 left unjudged).
- **Table left as-is** (5 rows × 4 columns, within N5). The `maxAttempts` Behavior cell ("Includes the first delivery attempt") is not parallel with the other rows, which L4 would flag — fixing that means rewording a cell, i.e. `content` scope.
- **`fmt --write` not run.** The deterministic layer reported nothing to fix, and the `--toc` / `--join-cjk` / `--strip-emoji` flags are all either inapplicable (18 lines, English) or lossy.

The honest summary: this input was already at the format ceiling — the only `format`-legal readability wins left were paragraph splitting and one list conversion, and the remaining unjudged rules are mostly `content`-axis items that `scope=format` cannot legally reach.

Done. Report below.

## Completed: `output.md`

**scope** `format` · **level** `deep` · written to `output.md` — `input.md` untouched (no git repo here, so I did not write in place)

### Command results

| Command | Exit | Result |
|---|---|---|
| `audit input.md --scope=format --level 3` | `0` | 100.0 |
| `audit output.md --scope=format --level 3` | `0` | 100.0 |
| `verify input.md output.md --scope=format` | `0` | `status: pass` |
| `fmt output.md --check` | `0` | already canonical, no changes needed |
| `report input.md output.md --scope=format --level 3` | `0` | verify(format) 通过 |

`verify` JSON: `status: "pass"`, `hard_failures: []`, `warnings: []`, `unknowns: []`, `ok: true`. **No `unknown` anywhere — nothing here is an unknown being dressed up as a pass.** Note what `pass` covers: the declared machine checks only (protected values, code fences, block mapping). It is not a proof of semantic equivalence.

### Script score 100.0 → 100.0 (+0.0)

| Dimension | Weight | Before | After |
|---|---|---|---|
| Hook / 首屏结论力 | 18% | 100.0 | 100.0 |
| Chunking / 分块粒度 | 18% | 100.0 | 100.0 |
| Scanability / 扫读性 | 13% | 100.0 | 100.0 |
| Sentence load / 句子负荷 | 13% | 100.0 | 100.0 |
| Actionability / 行动性 | 12% | 100.0 | 100.0 |
| Typography / 排版一致性 | 13% | 100.0 | 100.0 |
| Human feel / 活人感 | 13% | 100.0 | 100.0 |

The input was already clean on every deterministic axis, so this is a script score, not a final score.

**Anti-pattern deductions (X group): −0 → −0** (`x_hits: {}`). No X1 emoji, X2 fragmentation, X5 over-bolding, etc.

**Unjudged rules — not passes.** The score line reports **32 rules needing model judgment**, counted as not-hit and unscored: S4, S5, S6, S8, H3, H4, P2, P5, L2, L4, L7, W2, W3, W5, W7, W8, W9, A1, A2, A3, A5, A6, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8. Rule coverage at deep·format: **41 applicable** — 23 script-checked (scored), 5 hint-only (S7, L6, N3, T5, C6 — no points either way), 10 judge-only on the F axis (S5, S6, P2, P5, L2, N4, T3, X6, X7, X8), 2 auto-fix-only (P3, T6), 1 hard gate (X4, passed via verify).

### What changed

- **Split the 3-sentence note paragraph into two** — the auth-error exception (`401`/`403` never retried) now stands as its own block instead of hiding as sentence 3 of 3. Split at an existing sentence boundary; zero words touched.
- **Split the closing 2-sentence paragraph** — the restart requirement and the unit notes are now separate blocks.
- **Semicolon-joined parallel clause → 2-item list** — `` `visibilitySeconds` is measured in seconds; `backoffMs` is measured in milliseconds. `` becomes two bullets, original wording reused verbatim.

Character-level accounting: **all 99 words identical and in identical order**; the only punctuation delta is the `;` at the clause break, which became `.` when the clause became a list item. Inline code values, numbers/ranges (`45`, `5–600`, `1–8`, `100–5000`, `401`, `403`), units, identifiers, the `yaml` fence tag, and the code-block body are byte-identical.

### Deliberately not changed

- **No block reordering.** The restart caveat at the end is arguably the loudest candidate for S5 hoisting, but the task requires preserving the ordering of information, and `deep` skeleton guidance for reference docs says the quick-reference table stays first and stable. Moving the caveat above the table would break lookup-by-scan and risk dangling references.
- **No TL;DR, time estimate, next-step line, or "what you'll be able to do" (H1/H2/H3/H4, A1/A2/A5).** All require writing new text — that is the `content` axis. They remain unjudged, not satisfied.
- **No new headings.** "Notes" / "Example" would be new words (S8, S6 partly unreachable under `format`).
- **No bolding or `> **注意**` labels.** The source has no bold and no warning labels; adding them means new characters, and emphasis-vs-key-term (T3) is the wrong trade for a parameter reference.
- **`<details>` folding skipped.** The YAML example and both notes are main-path content — folding them would be X7 abuse (N4 left unjudged).
- **Table left as-is** (5 rows × 4 columns, within N5). The `maxAttempts` Behavior cell ("Includes the first delivery attempt") is not parallel with the other rows, which L4 would flag — fixing that means rewording a cell, i.e. `content` scope.
- **`fmt --write` not run.** The deterministic layer reported nothing to fix, and the `--toc` / `--join-cjk` / `--strip-emoji` flags are all either inapplicable (18 lines, English) or lossy.

The honest summary: this input was already at the format ceiling — the only `format`-legal readability wins left were paragraph splitting and one list conversion, and the remaining unjudged rules are mostly `content`-axis items that `scope=format` cannot legally reach.
