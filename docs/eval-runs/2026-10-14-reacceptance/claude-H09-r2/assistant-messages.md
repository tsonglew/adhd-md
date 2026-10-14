I'll start by reading the skill snapshot and the input file.

Now let me read the input, prompt, and key reference files.

Now let me examine the script's CLI interface and run the initial audit.

No need for a `/tmp` backup — I'm writing to `output.md`, not in place. Running the baseline audit:

Baseline script score is 100.0 with no format-scope findings. Let me inspect the JSON for exact rule status and anti-pattern deductions.

Let me read the doc-types reference (needed for S6 at level=deep) and inspect the verify implementation.

Let me inspect the tokenizer used by verify so my changes are predictable.

Let me check whether the deterministic fixer wants any changes (preview only, no write):

The input is already format-clean per `fmt`. Now let me draft a format-only candidate (listify the parallel rules, split the multi-topic final paragraph) and test it.

Verify passes and the score holds at 100.0 with zero findings. Let me capture exact exit codes and the before→after report.

Let me run rigorous preservation checks on the output.

Done. Here's the report.

## Reformat complete: `input.md` → `output.md`

**scope** `format` · **level** `deep` (=3) · written to `output.md` — `input.md` untouched (783 bytes before and after; mtime unchanged)

**Commands run (exit status)**

| Command | Exit | Result |
|---|---|---|
| `audit input.md --level 3 --scope=format` | `0` | script score 100.0, 0 findings |
| `audit output.md --level 3 --scope=format` | `0` | script score 100.0, 0 findings |
| `verify input.md output.md --scope=format` | `0` | **`pass`** (not `unknown`) |
| `report input.md output.md --scope=format --level 3` | `0` | no anti-pattern deduction, verify pass |
| `fmt input.md` / `fmt output.md` (preview) | `0` | "格式已规范，无需修改" — no deterministic fixes pending |

**Script score 100.0 → 100.0 (+0.0)** — this is the *script* score, not a final score. The script computes it over all axes regardless of scope and counts the 32 model-judged rules as un-hit; it is explicitly not a pass for those.

| Dimension | before | after |
|---|---|---|
| Hook (首屏结论力, 18%) | 100.0 | 100.0 |
| Chunking (18%) | 100.0 | 100.0 |
| Scannability (13%) | 100.0 | 100.0 |
| Sentence load (13%) | 100.0 | 100.0 |
| Actionability (12%) | 100.0 | 100.0 |
| Typography (13%) | 100.0 | 100.0 |
| Human-ness (13%) | 100.0 | 100.0 |

**Anti-pattern deductions: −0 → −0** (`x_deduct: 0`, `x_hits: {}`). X1/X2/X5 are script-checked with 0 hits (no emoji, no fragmentation, 0 bold); X4 is the verify hard gate and passes; X3/X6/X7/X8 are model-judged — see the table below, no hits.

**Unjudged rules — my verdicts (32 rules the script did not score; none is reported as a pass by default)**

Scope note: the format-scope slice has 10 model-judged rules; the other 22 are C-axis (content) rules that `scope=format` cannot touch. `H1`/`H2` (TL;DR rules) are also content-axis and are **not** in effect here — the hook dimension's 100.0 does **not** mean a TL;DR exists.

| Rule | Verdict | Basis (output location / reason) |
|---|---|---|
| S4 heading states conclusion | Not satisfied (scope limit) | Only heading is the module name (`output.md:1`); rewording needs content permission |
| S5 conclusion block first | Not applicable | Source has no conclusion/summary block; the highest-value block (quick-reference table) is already first |
| S6 section order matches reference skeleton | Satisfied | Reference skeleton wants 速查表 first; table sits directly under H1 (`output.md:3`) |
| S8 each section opens with its purpose | Not applicable | No subsections; adding a lead sentence = new words |
| H3 first screen states reader payoff | Not satisfied (scope limit) | Requires a sentence not present in the source |
| H4 time/length estimate up front | Not satisfied (scope limit) | No reading time or step count exists in the source; `format` forbids adding wording |
| P2 one topic per paragraph | Satisfied | Was mixed; final paragraph split at its sentence boundary (`output.md:18`, `:20`) |
| P5 over-long blockquote | Not applicable | No blockquotes |
| L2 enumerable parallel sentences → list | Satisfied | Two parallel retry rules now list items, original wording verbatim (`output.md:12-13`) |
| L4 parallel list structure | Satisfied | Both items are complete present-tense declarative sentences |
| L7 list items keep full meaning | Satisfied | Each item carries subject + predicate; readable standalone |
| W2 active voice | Not satisfied (scope limit) | "are never retried", "is measured" are passive; rewording is content |
| W3 parenthetical split out | Not applicable | (`401` and `403`) is 3 words, below the >5-word threshold |
| W5 explain terms at first use | Not applicable | No unexplained abbreviations; keys are defined in the table |
| W7 second person / present / concrete verbs | Not applicable | Reference doc contains no instructional sentences |
| W8 one clause per sentence | Satisfied | No sentence has three-level nesting |
| W9 negatives → positive statements | Satisfied | "never retried" / "disables retries" are exception semantics W9 says to keep |
| A1 next step at section end | Not applicable | No executable sections |
| A2 time estimate per step | Not applicable | No steps |
| A3 default recommendation | Not applicable | No option sets |
| A5 "do this one thing" | Not applicable | Short reference doc, not a long document |
| A6 decision criteria | Not applicable | No decision points |
| A7 expected output per step | Not applicable | No executable steps (the YAML block is an example config, not a command) |
| A8 one action per step | Not applicable | No steps |
| N4 fold optional content | Not applicable | Nothing deviates from the main path; folding the table/YAML would hide main-path content (X7) |
| N7 multi-step progress markers | Not applicable | No ≥4-step flow |
| C4 Chinese long-attribute rule | Not applicable | Document language is `en` |
| T3 consistent marker semantics | Satisfied | Inline code only for literals; no bold/italic introduced |
| X3 keywords instead of sentences | No hit | All list items are full sentences |
| X6 table abuse | No hit | Homogeneous comparable data; short cells |
| X7 folding abuse | No hit | No `<details>` |
| X8 template stuffing | No hit | No repeated boilerplate subsections |

**What I changed**
- Split the `maxAttempts` paragraph at existing sentence boundaries: the two parallel retry rules became list items, reusing the original words exactly (`output.md:10-13`) — L2/P2.
- Split the final paragraph at its sentence boundary: restart behavior and unit notes are now one topic each (`output.md:18`, `:20`) — P2.
- Nothing else: no word, number, unit, condition, exception, link, or code block was altered; ordering of information is unchanged.

**What I deliberately did not change**
- No TL;DR, no reading-time line, no "what you'll be able to do", no extra headings, no bold, no dividers, no TOC: all would be new wording (content) or noise on a 20-line reference doc; adding them would hard-fail `verify --scope=format` as `prose_tokens_added`.
- Table, YAML block, and both caveat facts left in place — the reference skeleton's "quick-reference first" is already satisfied, and reordering would violate the required information order.
- Passive voice, heading wording, and the missing lead-in sentence left as-is: they are real gaps, but fixing them needs `content` permission. Recorded as "Not satisfied (scope limit)" above, not as passes.

**What `verify --scope=format` does and does not cover:** `pass` means the declared machine checks ran clean — code-block bodies, inline literals, link targets, numeric literals, frontmatter, and prose-token multiset are unchanged (I also confirmed the original character stream is byte-identical after stripping the added list markers). It does not prove sentence-level semantic equivalence, and it does not validate any of the 32 judged rules above. No `unknown` occurred in this run; had one occurred, it would be reported as unresolved rather than as a pass.

Done. Here's the report.

## Reformat complete: `input.md` → `output.md`

**scope** `format` · **level** `deep` (=3) · written to `output.md` — `input.md` untouched (783 bytes before and after; mtime unchanged)

**Commands run (exit status)**

| Command | Exit | Result |
|---|---|---|
| `audit input.md --level 3 --scope=format` | `0` | script score 100.0, 0 findings |
| `audit output.md --level 3 --scope=format` | `0` | script score 100.0, 0 findings |
| `verify input.md output.md --scope=format` | `0` | **`pass`** (not `unknown`) |
| `report input.md output.md --scope=format --level 3` | `0` | no anti-pattern deduction, verify pass |
| `fmt input.md` / `fmt output.md` (preview) | `0` | "格式已规范，无需修改" — no deterministic fixes pending |

**Script score 100.0 → 100.0 (+0.0)** — this is the *script* score, not a final score. The script computes it over all axes regardless of scope and counts the 32 model-judged rules as un-hit; it is explicitly not a pass for those.

| Dimension | before | after |
|---|---|---|
| Hook (首屏结论力, 18%) | 100.0 | 100.0 |
| Chunking (18%) | 100.0 | 100.0 |
| Scannability (13%) | 100.0 | 100.0 |
| Sentence load (13%) | 100.0 | 100.0 |
| Actionability (12%) | 100.0 | 100.0 |
| Typography (13%) | 100.0 | 100.0 |
| Human-ness (13%) | 100.0 | 100.0 |

**Anti-pattern deductions: −0 → −0** (`x_deduct: 0`, `x_hits: {}`). X1/X2/X5 are script-checked with 0 hits (no emoji, no fragmentation, 0 bold); X4 is the verify hard gate and passes; X3/X6/X7/X8 are model-judged — see the table below, no hits.

**Unjudged rules — my verdicts (32 rules the script did not score; none is reported as a pass by default)**

Scope note: the format-scope slice has 10 model-judged rules; the other 22 are C-axis (content) rules that `scope=format` cannot touch. `H1`/`H2` (TL;DR rules) are also content-axis and are **not** in effect here — the hook dimension's 100.0 does **not** mean a TL;DR exists.

| Rule | Verdict | Basis (output location / reason) |
|---|---|---|
| S4 heading states conclusion | Not satisfied (scope limit) | Only heading is the module name (`output.md:1`); rewording needs content permission |
| S5 conclusion block first | Not applicable | Source has no conclusion/summary block; the highest-value block (quick-reference table) is already first |
| S6 section order matches reference skeleton | Satisfied | Reference skeleton wants 速查表 first; table sits directly under H1 (`output.md:3`) |
| S8 each section opens with its purpose | Not applicable | No subsections; adding a lead sentence = new words |
| H3 first screen states reader payoff | Not satisfied (scope limit) | Requires a sentence not present in the source |
| H4 time/length estimate up front | Not satisfied (scope limit) | No reading time or step count exists in the source; `format` forbids adding wording |
| P2 one topic per paragraph | Satisfied | Was mixed; final paragraph split at its sentence boundary (`output.md:18`, `:20`) |
| P5 over-long blockquote | Not applicable | No blockquotes |
| L2 enumerable parallel sentences → list | Satisfied | Two parallel retry rules now list items, original wording verbatim (`output.md:12-13`) |
| L4 parallel list structure | Satisfied | Both items are complete present-tense declarative sentences |
| L7 list items keep full meaning | Satisfied | Each item carries subject + predicate; readable standalone |
| W2 active voice | Not satisfied (scope limit) | "are never retried", "is measured" are passive; rewording is content |
| W3 parenthetical split out | Not applicable | (`401` and `403`) is 3 words, below the >5-word threshold |
| W5 explain terms at first use | Not applicable | No unexplained abbreviations; keys are defined in the table |
| W7 second person / present / concrete verbs | Not applicable | Reference doc contains no instructional sentences |
| W8 one clause per sentence | Satisfied | No sentence has three-level nesting |
| W9 negatives → positive statements | Satisfied | "never retried" / "disables retries" are exception semantics W9 says to keep |
| A1 next step at section end | Not applicable | No executable sections |
| A2 time estimate per step | Not applicable | No steps |
| A3 default recommendation | Not applicable | No option sets |
| A5 "do this one thing" | Not applicable | Short reference doc, not a long document |
| A6 decision criteria | Not applicable | No decision points |
| A7 expected output per step | Not applicable | No executable steps (the YAML block is an example config, not a command) |
| A8 one action per step | Not applicable | No steps |
| N4 fold optional content | Not applicable | Nothing deviates from the main path; folding the table/YAML would hide main-path content (X7) |
| N7 multi-step progress markers | Not applicable | No ≥4-step flow |
| C4 Chinese long-attribute rule | Not applicable | Document language is `en` |
| T3 consistent marker semantics | Satisfied | Inline code only for literals; no bold/italic introduced |
| X3 keywords instead of sentences | No hit | All list items are full sentences |
| X6 table abuse | No hit | Homogeneous comparable data; short cells |
| X7 folding abuse | No hit | No `<details>` |
| X8 template stuffing | No hit | No repeated boilerplate subsections |

**What I changed**
- Split the `maxAttempts` paragraph at existing sentence boundaries: the two parallel retry rules became list items, reusing the original words exactly (`output.md:10-13`) — L2/P2.
- Split the final paragraph at its sentence boundary: restart behavior and unit notes are now one topic each (`output.md:18`, `:20`) — P2.
- Nothing else: no word, number, unit, condition, exception, link, or code block was altered; ordering of information is unchanged.

**What I deliberately did not change**
- No TL;DR, no reading-time line, no "what you'll be able to do", no extra headings, no bold, no dividers, no TOC: all would be new wording (content) or noise on a 20-line reference doc; adding them would hard-fail `verify --scope=format` as `prose_tokens_added`.
- Table, YAML block, and both caveat facts left in place — the reference skeleton's "quick-reference first" is already satisfied, and reordering would violate the required information order.
- Passive voice, heading wording, and the missing lead-in sentence left as-is: they are real gaps, but fixing them needs `content` permission. Recorded as "Not satisfied (scope limit)" above, not as passes.

**What `verify --scope=format` does and does not cover:** `pass` means the declared machine checks ran clean — code-block bodies, inline literals, link targets, numeric literals, frontmatter, and prose-token multiset are unchanged (I also confirmed the original character stream is byte-identical after stripping the added list markers). It does not prove sentence-level semantic equivalence, and it does not validate any of the 32 judged rules above. No `unknown` occurred in this run; had one occurred, it would be reported as unresolved rather than as a pass.
