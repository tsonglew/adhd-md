# Search results are stale

Scope: this runbook covers the dashboard search index. It does not cover billing exports or direct database queries.

## Confirm the issue

- A record changed more than 5 minutes ago but the dashboard shows its previous value.
- The record is visible in the primary database.
- No index maintenance is in progress.

If the primary database does not contain the record, follow the write-failure runbook instead.

## Recovery

1. Record the workspace ID, record ID, and last update time.
2. Check the indexer queue depth and save the metric value.
3. If the queue is nonzero, wait 3 minutes and refresh the dashboard once.
4. If the value is still stale, requeue only the affected workspace.
5. Confirm the updated value appears before closing the incident.

Do not rebuild the global index during business hours. Requeueing does not modify the primary database.
