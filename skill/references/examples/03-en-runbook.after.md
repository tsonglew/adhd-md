# Payments API 5xx

Most incidents are one of two things: **Redis pool exhaustion** or a **slow ledger query**. Check those first. Escalate after 15 minutes.

Dashboard: [payments 5xx by route](https://grafana.internal/d/payments)

## Step 1 — Was there a deploy in the last 30 minutes?

```bash
kubectl rollout history deploy/payments -n prod
```

If yes, roll it back. Takes about 90 seconds to take effect.

```bash
kubectl rollout undo deploy/payments -n prod
```

## Step 2 — Is the Redis pool exhausted?

```bash
redis-cli -h payments-redis info clients
```

`connected_clients` above 4500 (of 5000 max) means the pool is exhausted.

Fix: scale the deployment down to 0 and back up.

> **Warning**: this drops in-flight requests. Only do it if the error rate is above 5%.

## Step 3 — Is the ledger service slow?

Payments depends on the ledger service and on Redis, so a slow ledger query surfaces as payments 5xx. Check ledger p99 latency. Above 800ms, page the ledger on-call instead of continuing to debug payments.

## Still broken? Escalate

Do not spend more than 15 minutes before escalating. Escalate to the payments on-call lead in `#payments-oncall` with:

- [ ] Incident ID
- [ ] Output of the two commands above
- [ ] Screenshot of the "5xx by route" panel

## Afterwards

- [ ] File an incident report within 24 hours
- [ ] Add any new symptom to this runbook
