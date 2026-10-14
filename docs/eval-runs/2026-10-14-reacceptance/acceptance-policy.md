# Reacceptance policy

Frozen before reviewing outputs. Test current uncommitted working-tree skill exactly as hashed in skill-snapshot.json; no tuning during this run.

- Regress H01–H12 on Codex and Claude Code, repeating H03/H06/H09/H12 three times (40 runs). R01 on both hosts checks the final A8/S4 clarification (2 more runs). Retry the other four hosts once and retain all failures.
- Use the original prompts verbatim and the preannotated constraints in the corpus manifest. H04 is evaluated against the input's inclusive 100,000 boundary, not the historical key's incorrect strict-less-than wording.
- Independent harness audit/verify/report must use the declared scope and level. Check actual model tool calls separately. CLI exit zero is not output success, and script score 100 is not complete compliance.
- Format acceptance requires verifier pass, zero X deduction, preserved original prose characters/punctuation/order and protected literals. Presentation markers may change; exact-byte copying is a valid safe fallback. A changed unknown candidate cannot be accepted as completed output.
- Content review checks every source fact, condition, exception, value, prerequisite, original code/link and layout style. No source-free product or UI facts. Conditions must govern all resulting actions.
- Review judge-rule decisions and their evidence separately from machine checks. Legitimate scope/source limitations must be declared; a fabricated fact to satisfy a rule is a failure. Check H4/N7 completion where applicable and A8/S4 boundary interpretation; do not require impossible source-free outcomes for A7.
- A discovered regression is retained even if the model self-reports pass. No cherry-picking or retries replacing earlier attempts.
- Review is by the coordinator against preannotated constraints, not independent human signoff. The checklist explicitly permits preannotated-constraint review as an alternative; record human status honestly. Other hosts may remain unverified, but may not be advertised as verified.
- This is a regression acceptance run, not a new blind evaluation. Previously exposed cases cannot establish held-out generalization.
