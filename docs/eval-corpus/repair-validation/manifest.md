# Repair validation v1

Frozen before model execution on 2026-10-14. These are new repair-validation cases, not a replacement for the complete EVAL-01 held-out matrix. No answer key is sent to the models.

- content.md: English, runbook, content/deep. Retain paragraph/list/inline styles; every original condition, exception, order and boundary; add no UI facts. Judge all in-scope rules, with evidence.
- format.md: Chinese, reference, format/deep. Preserve punctuation, words, comment and literals. Unknown must produce unchanged output, not an accepted edited candidate.

Expected review: conditional wait and reload remain together under the active-lock guard; session/manual limitation and archived exception survive; accepted is not completion. Boundary includes exactly 75,000. No fabricated outcomes for opening/selecting/copying. Explicit level 3 in audit/report.
