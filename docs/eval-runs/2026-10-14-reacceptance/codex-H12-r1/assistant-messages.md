I’ll use the adhd-md skill for a deep, format-only pass, write `output.md`, and check preservation and readability with the requested scripts.

The audit reports 97.4/100, and the formatter proposes no changes. The only finding is bold density at 8.3%; I’ll preserve those markers under your character-preservation constraint and check whether spacing can make the nested steps easier to scan.

`output.md` now has two added blank lines around the nested checks. Every original byte remains in order, and `verify --scope=format` returned `pass` with exit status 0. The script score remains 97.4, with zero anti-pattern deductions; I’m documenting the rules the script leaves unjudged.

Created [output.md](/private/tmp/adhd-reacceptance-20261014/codex-H12-r1/workspace/output.md) using `scope=format`, `level=deep`. Added only two blank lines; every original character and its order remain intact. Input unchanged.

- **Audit:** exit 0.
- **Verify:** `pass`, exit 0; no unknowns.
- **Script score:** 97.4 → 97.4; all dimension deltas 0.
- **Anti-pattern deductions:** 0 → 0.
- **Script-unjudged rules:** 32 overall, 10 within format scope.

Original emphasis was deliberately preserved, leaving T2d’s 8.3% bold-density finding. H4, A7, and conservatively A8 remain unmet. All rule assessments and command results are in [output.report.md](/private/tmp/adhd-reacceptance-20261014/codex-H12-r1/workspace/output.report.md).
