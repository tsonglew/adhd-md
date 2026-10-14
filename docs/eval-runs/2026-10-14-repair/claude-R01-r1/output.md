# Thumbnail recovery

Retry a failed thumbnail job. The procedure has 4 steps, and one of them adds a 7-minute wait when the job's lock is active.

Manual retry settings apply only to this browser session. Signing in elsewhere does not copy those manual settings. Do not retry jobs marked archived.

1. Step 1 of 4 — Open the job panel. Select a failed job.
2. Step 2 of 4 — If the job's lock is active, wait 7 minutes. When the wait is over, reload the panel once.
3. Step 3 of 4 — Copy the job key into the incident note.
4. Step 4 of 4 — Submit the retry request. Expected: status accepted.

A successful request shows status accepted. Accepted does not mean the thumbnail has finished rendering.
