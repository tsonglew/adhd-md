# Queue configuration

| Setting | Default | Valid range | Behavior |
|---|---:|---:|---|
| `visibilitySeconds` | 45 | 5–600 | Time before an unacknowledged job is visible again |
| `maxAttempts` | 3 | 1–8 | Includes the first delivery attempt |
| `backoffMs` | 400 | 100–5000 | Base delay between retry attempts |
| `deadLetterAfter` | 8 | 1–20 | Failed jobs moved to the dead-letter queue |

`maxAttempts` counts the initial delivery. A value of `1` disables retries.

Authentication errors (`401` and `403`) are never retried, even when `maxAttempts` is greater than one.

```yaml
queue:
  maxAttempts: 4
  backoffMs: 800
```

Configuration changes take effect after the worker restarts.

`visibilitySeconds` is measured in seconds; `backoffMs` is measured in milliseconds.
