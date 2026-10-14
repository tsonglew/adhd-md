# Recover stale dashboard search results

Scope: this runbook covers the dashboard search index. It does not cover billing exports or direct database queries.

## Confirm all recovery prerequisites

- The record changed more than 5 minutes ago, but the dashboard still shows its previous value.
- The primary database contains the record.
- No index maintenance is in progress.

If the primary database does not contain the record, use the write-failure runbook instead.

## Recover only the affected workspace in five steps

1. Record the workspace ID, record ID, and last update time.
2. Save the indexer queue depth metric value.
3. If the queue is nonzero, wait 3 minutes. Then refresh the dashboard once.
4. If the value is still stale, requeue only the affected workspace.
5. Before closing the incident, confirm that the dashboard shows the updated value.

Do not rebuild the global index during business hours. Requeueing does not modify the primary database.
