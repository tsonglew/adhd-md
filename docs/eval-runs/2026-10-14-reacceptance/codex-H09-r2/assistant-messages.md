I’ll use the adhd-md skill for a deep, format-only pass, save it as `output.md`, and run the requested checks while preserving `input.md`.


The initial audit scores 100/100, but leaves 32 rules for manual judgment. The reference table is already well structured. I’ll make the surrounding notes easier to scan with full-sentence bullets and sparse emphasis. The missing reading estimate will remain unmet because adding one would violate your content-preservation constraint.


`output.md` passes `verify --scope=format` with exit code 0 and no unknowns. The audit remains 100/100 with zero anti-pattern deductions. A separate check confirms that every original character remains in order and `input.md` is unchanged. I’m recording the manual rule judgments separately so the script score isn’t presented as full compliance.


Created [output.md](/private/tmp/adhd-reacceptance-20261014/codex-H09-r2/workspace/output.md) using `scope=format`, `level=deep`. Added bullets and sparse emphasis; every original character remains in order. `input.md` is unchanged.

- **Audit:** exit `0`; script score **100 → 100**, all dimension deltas `0`.
- **Anti-pattern deductions:** **0 → 0**.
- **Verify:** exit `0`, **pass**; no warnings or unknowns.
- **Unjudged rules:** the script leaves 32 unjudged. All are manually assessed in the [review](/private/tmp/adhd-reacceptance-20261014/codex-H09-r2/workspace/review.md). H4’s reading estimate remains unmet because adding content was prohibited.

The script score is not a claim that every rule passed.
