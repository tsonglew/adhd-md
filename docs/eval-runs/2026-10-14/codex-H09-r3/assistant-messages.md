I’ll use the adhd-md skill to reformat `input.md` at the deep level, preserve the source content and order, and check `output.md` with both required commands.

The reference table already works well for lookup. I’ve separated the retry exception and unit definitions into their own paragraphs while keeping the original order. The audit flagged excess bolding, so I’m reducing it before the final checks.

Created [output.md](/private/tmp/adhd-eval-20261014/codex-H09-r3/workspace/output.md) using `scope=format`, `level=deep`. Input unchanged.

- Changed: paragraph spacing and two short emphasis spans.
- Deliberately preserved: wording, punctuation, numbers, units, conditions, exceptions, table, code, and information order.
- `audit`: exit **0**, no findings.
- `verify --scope=format`: exit **0**, **pass**; no warnings or unknowns.
- Script score: **100 → 100**. All seven dimensions unchanged at 100 (delta 0).
- Anti-pattern deductions: **0 → 0**.

The script leaves 32 rules unjudged—not passed: S4, S5, S6, S8, H3, H4, P2, P5, L2, L4, L7, W2, W3, W5, W7, W8, W9, A1, A2, A3, A5, A6, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8. The score is script-only; verification covers its declared checks.
