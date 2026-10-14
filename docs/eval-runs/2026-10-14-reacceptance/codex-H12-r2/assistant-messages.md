I’ll use the adhd-md skill to reformat `input.md` at `scope=format`, `level=deep`, then check `output.md` with `audit` and `verify` while leaving the input untouched.

The formatter found no automatic fixes. The audit’s only finding is bold density at 8.3%, slightly above its 8% limit; I’ll preserve the original emphasis markers under your character-preservation requirement and check whether spacing changes can safely improve readability.

`output.md` now adds two blank lines around the nested preview checks. Every original character remains in order, and `verify --scope=format` passed with exit status 0 and no unknowns. The score remains 97.4; I’m recording the remaining finding and rule-by-rule judgments in a separate report.

Created [output.md](/private/tmp/adhd-reacceptance-20261014/codex-H12-r2/workspace/output.md) using `scope=format`, `level=deep`. Added only two blank lines; every original character and its order are preserved. Input unchanged.

- **Audit:** exit 0; script score **97.4 → 97.4**, all dimension deltas 0.
- **Verify:** `pass`, exit 0; no warnings or unknowns.
- **Anti-pattern deductions:** **0 → 0**.
- **Remaining finding:** bold density 8.3% exceeds 8%; original markers preserved.
- **Script-unjudged rules:** 32, individually reviewed in the [report](/private/tmp/adhd-reacceptance-20261014/codex-H12-r2/workspace/report.md). Unmet and inapplicable rules are explicitly identified; full compliance is not claimed.
