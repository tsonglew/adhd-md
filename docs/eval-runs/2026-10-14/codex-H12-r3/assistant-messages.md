I’ll use the adhd-md skill to reformat `input.md` at the deep level, preserve its content and order, and check `output.md` with the required audit and verification commands.


The audit reports 149% bold density, which appears to be a parser error involving the literal `x ** 2`. I’ll preserve that expression and all existing markers, make only spacing changes, and report any remaining deduction accurately.


Created [output.md](output.md) using `scope=format`, `level=deep`. Added two blank lines around the nested checks. Input unchanged; all original characters and ordering preserved.

- **Audit:** exit `0`; script score **91.4 → 91.4**.
- **Dimensions:** formatting consistency **80 → 80**; all six others **100 → 100**.
- **Verify:** exit `0`, **pass** for implemented checks.
- **Anti-pattern deduction:** **−6 → −6 (X5)**. The parser misreads literal `x ** 2` as bold markup. Preserving it leaves the zero-deduction requirement unmet; `report` exits `1`.

Deliberately retained all wording, markers, code, links, and structure.

**Unjudged rules—not passes:** S4, S5, S6, S8, H3, H4, P2, P5, L2, L4, L7, W2, W3, W5, W7, W8, W9, A1, A2, A3, A5, A6, A7, A8, N4, N7, T3, C4, X3, X6, X7, X8.
