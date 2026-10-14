I’ll use the adhd-md skill to rewrite `input.md`, preserve the specified details, and check `output.md` with the required audit and content report.

The input already scores 100.0 on the script checks. I’ll make small wording changes while keeping the existing layout and all constraints. The script leaves several rules unjudged, so that score is not a complete quality assessment.

Created [output.md](output.md); `input.md` is unchanged.

Used `scope=content`, `level=standard`. Shortened wording and clarified headings. Deliberately preserved the layout, steps, numbers, units, restrictions, and exceptions.

Ran `audit` and `report --scope=content`:

- **Script score:** 100.0 → 100.0.
- **Dimension deltas:** first-screen clarity, chunking, scanning, sentence load, actionability, formatting, and naturalness: all **0.0**.
- **Anti-pattern deductions:** 0 → 0.
- **verify(content): PASS**, with no warnings or unknowns. This covers declared machine checks, not complete semantic equivalence.
- **Unjudged content rules:** S4, H4, L4, L7, W2, W3, W5, W8, A1, A7, A8, N7, C4, X3. These are **not passes**; the score is script-only.
