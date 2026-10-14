# Search rollout review · 2026-09-22

**Outcome**

- The new search index reached 100% of workspaces.
- Median query time is 210 ms against a target below 250 ms.
- The 95th percentile is 680 ms, above the 600 ms target.

**Decisions**

- Keep the rollout at 100% while the error rate stays below 0.5%.
- Do not enable fuzzy matching until the 95th percentile is below 600 ms for three consecutive days.
- Recheck mobile query time separately; desktop data does not cover it.

**Actions**

- [ ] Alex: add mobile latency to the dashboard by Friday.
- [ ] Search team: report three daily percentile values next week.

**Rollback trigger**

If the error rate exceeds 1% for 10 consecutive minutes, return to the previous index version.

A single slow query is not a rollback trigger.
