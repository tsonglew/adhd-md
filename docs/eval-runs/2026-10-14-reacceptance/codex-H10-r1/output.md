# Recover stale dashboard search results (5 steps)

Scope: this runbook covers the dashboard search index. It does not cover billing exports or direct database queries.

## Confirm all conditions before recovery

- The record changed more than 5 minutes ago. The dashboard still shows its previous value.
- The record is visible in the primary database.
- No index maintenance is in progress.

If the record is missing from the primary database, follow the write-failure runbook instead. If all three conditions hold, proceed to recovery.

## If the value stays stale, requeue only the affected workspace

1. Step 1 of 5: Record the workspace ID (identifier), record ID, and last update time.
2. Step 2 of 5: Check the indexer queue depth. Save the metric value.
3. Step 3 of 5: If the queue is nonzero, wait 3 minutes and then refresh the dashboard once.
4. Step 4 of 5: If the dashboard value is still stale, requeue only the affected workspace.
5. Step 5 of 5: Confirm the updated value appears before closing the incident.

Do not rebuild the global index during business hours. Requeueing does not modify the primary database.
