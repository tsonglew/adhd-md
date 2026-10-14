# Search results are stale

Scope: this runbook covers the dashboard search index. It does not cover billing exports or direct database queries.

Check the three signs, then work the six recovery steps in order. Requeueing does not modify the primary database.

## Confirm the three signs

- A record changed more than 5 minutes ago, but the dashboard still shows its previous value.
- The record is visible in the primary database.
- No index maintenance is in progress.

If the primary database does not contain the record, follow the write-failure runbook instead.

## Recovery — 6 steps

Do not rebuild the global index during business hours.

1. Record the workspace ID, record ID, and last update time. You will use these three values for the requeue and the final confirmation.
2. Check the indexer queue depth and save the metric value. A nonzero depth means the indexer is still behind.
3. If the queue is nonzero, wait 3 minutes.
4. Refresh the dashboard once.
5. If the value is still stale, requeue only the affected workspace.
6. Confirm the updated value appears before you close the incident.
