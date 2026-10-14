# Formatting report

Applied `scope=format`, `level=standard` (`--level 2`) using `.agents/skills/adhd-md/SKILL.md`. Output: [output.md](output.md). The input was not overwritten.

Added blockquote styling to the prerequisite and failure branch, three short bold spans, and blank lines between the six numbered steps. Removing only those additions restores `input.md` byte for byte: all original characters, whitespace, punctuation, numbers, units, inline code, conditions, exceptions, and information order are preserved. There were no original links or fenced code blocks.

Deliberately unchanged: wording, headings, step numbers, compound actions, and all information order. No summary, timing estimate, progress labels, terminology definitions, or new verification behavior was added. The short failure branch remains fully visible.

## Executed checks

Raw machine results and exact commands are saved in [validation.json](validation.json).

| Check | Scope / level | Exit status | Result |
|---|---|---|---|
| `audit input.md` | format / 2 | 0 | Script score 100.0; no findings |
| `fmt input.md` preview | format preview; no write | 0 | No deterministic changes suggested |
| `audit output.md` | format / 2 | 0 | Script score 100.0; no findings |
| `verify input.md output.md --scope=format` | format | 0 | `pass`; no hard failures, warnings, or unknowns |
| `report input.md output.md` | format / 2 | 0 | Score and deductions unchanged; verification passed |
| Exact restoration check | Remove only added formatting | 0 | Restored bytes equal `input.md` |

The text and JSON versions of the audit, verify, and report commands all exited 0. `validation.json` contains the JSON runs; the formatter preview and exact restoration check were run separately.

The restoration check removes the added `> ` prefixes and `**` markers, then removes the five inserted blank lines before steps 2–6. This stricter check covers punctuation and order beyond the verifier's normal format allowances. The verifier's `pass` describes its supported machine checks; it is not a claim that every readability rule is satisfied. No `unknown` result is treated as a pass.

## Script scores

Script score: **100.0 → 100.0 (+0.0)**. The script does not calculate a complete score including manual judgments; its score band is `null`.

| Dimension | Before | After | Delta |
|---|---|---|---|
| First-screen clarity | 100.0 | 100.0 | 0.0 |
| Chunking | 100.0 | 100.0 | 0.0 |
| Scannability | 100.0 | 100.0 | 0.0 |
| Sentence load | 100.0 | 100.0 | 0.0 |
| Actionability | 100.0 | 100.0 | 0.0 |
| Typography consistency | 100.0 | 100.0 | 0.0 |
| Natural writing | 100.0 | 100.0 | 0.0 |

Anti-pattern deductions: **0 → 0**; machine X hits: none. Manual review also found no X violations. M-group findings remain **0 → 0**.

Format/standard coverage: 39 applicable rules, comprising 23 script-checked rules, 4 advisory rules, 9 manual rules, 2 formatter-only rules, and 1 verification gate. Scope filters findings and coverage, while the script score covers all applicable axes.

## Rules left unjudged by the script

Both audits leave these 23 rules unjudged/unscored: **S4, S5, H4, P2, P5, L2, L4, L7, W2, W3, W5, W8, A1, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8**. Nine belong to the selected format scope. Every rule is reviewed below; manual assessments do not alter the reported script score. A content rule marked “Not met” is an existing limitation that this format-only request does not authorize fixing.

| Rule | Axis | Manual assessment | Output evidence and reason |
|---|---|---|---|
| S4 | Content | Not met | Line 5: “Steps” names a topic rather than a conclusion. Heading wording is preserved. |
| S5 | Format | Not applicable | Line 1 already states the tutorial task. Line 21 is a scope note, not an existing answer/summary block requiring relocation. The user also requires original order. |
| H4 | Content | Not met | Lines 1–7 contain no reading/task duration or explicit total-step estimate. “48 hours” on line 3 is a certificate-validity prerequisite, not a time estimate. Adding an estimate is prohibited. |
| P2 | Format | Met | Line 3 concerns safe readiness; line 19 concerns the failure branch; line 21 concerns unchanged service settings. Each paragraph has one topic. |
| P5 | Format | Not applicable | The two blockquotes at lines 3 and 19 are short; neither exceeds five source lines. |
| L2 | Format | Not applicable | Lines 7–17 already enumerate the procedure. The remaining prose contains conditions and warnings, not an unformatted parallel enumeration. |
| L4 | Content | Met | Lines 7–17 use imperative actions. Step 6 places its condition before “remove”; that condition remains attached. |
| L7 | Content | Met | Every numbered item retains its complete original instruction and object. |
| W2 | Content | Met | Lines 3–21 use active statements and imperatives; no passive instructions require rewriting. |
| W3 | Content | Not applicable | No parenthetical insertions occur. |
| W5 | Content | Not met | Line 11 first uses HTTPS without an explanation. Adding a definition would add content. |
| W8 | Content | Met | The prerequisite and conditional instructions contain no three-level nested clauses. |
| A1 | Content | Met | Line 17 provides the gated final cleanup action; line 19 provides concrete failure actions. No additional next action is needed to express the source procedure. |
| A7 | Content | Not met | Lines 7–9 pair upload with fingerprint verification; lines 11–13 pair staging deployment/request with status/date verification; lines 15–17 pair rollout with the all-instance fingerprint gate. The final removal has no explicit post-removal verification. No success behavior may be invented. |
| A8 | Content | Not met | Line 11 combines deployment and a request. Line 19 combines stopping and comparing under the same `495` condition. Splitting these into new instructions would disturb the exact wording/numbering constraints; their original grouping remains. |
| N4 | Format | Not applicable | The brief safety branch at line 19 should remain visible; there is no long optional material or existing optional heading to fold. |
| N7 | Content | Not met | Lines 7–17 retain numbering 1–6, but no “Step X of 6” labels. Adding those labels is prohibited. |
| T3 | Format | Met | Lines 3 and 19 use sparse bold for the prerequisite label and key constraints/actions. `/health`, `200`, and `495` retain inline-code styling as literal values. |
| C4 | Content | Not applicable | This is an English document; no Chinese attributive constructions occur. |
| X3 | Content | Met | Lines 7–17 retain complete meaningful instructions; no keyword fragments were introduced. |
| X6 | Format | Met | The output contains no tables. Narrative content remains prose. |
| X7 | Format | Met | The output contains no folding; every step and warning remains visible. |
| X8 | Format | Met | Original headings only; no repeated template headings or filler sections were added. |

No manual judgment remains unknown. S4, H4, W5, A7, A8, and N7 remain unmet; full-rule compliance is not claimed.

## Anti-pattern review

For this table, “Met” means the prohibition is respected.

| Rule | Assessment | Evidence |
|---|---|---|
| X1 | Met | No emoji in either document; no machine hit. |
| X2 | Met | The original two headings remain; no new sections; no machine fragmentation hit. |
| X3 | Met | Original complete instructions remain intact. |
| X4 | Met | `verify` returned `pass`; exact restoration confirms no original character or ordering was lost. |
| X5 | Met | Three short bold spans; no machine bold-density hit. |
| X6 | Met | No tables in `output.md`. |
| X7 | Met | No hidden content in `output.md`. |
| X8 | Met | No new headings or filler in `output.md`. |

## Preserved conditions and sequence

| Original requirement | Output location |
|---|---|
| Deployment-admin access AND current certificate valid for at least 48 hours | Line 3 |
| Do not remove the current certificate during the check | Line 3 |
| Upload to staging secret store, then compare fingerprint with approved change record | Lines 7–9 |
| Deploy to one staging instance and request `/health` over HTTPS | Line 11 |
| Confirm `200` AND the approved expiration date | Line 13 |
| Roll out to production one instance at a time | Line 15 |
| Remove old certificate only after all instances report the new fingerprint | Line 17 |
| If staging returns `495`, stop rollout AND compare chain with approved record | Line 19 |
| Keep current production certificate active while investigating | Line 19 |
| Renewal does not change service hostname OR client trust bundle | Line 21 |
