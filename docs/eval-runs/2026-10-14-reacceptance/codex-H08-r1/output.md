# Replace a service certificate

> **Prerequisite:** you have deployment-admin access, and the current certificate remains valid for **at least 48 hours**. Do not remove the current certificate during the check.

## Steps

1. Upload the replacement certificate to the staging secret store.

2. Confirm the displayed fingerprint matches the approved change record.

3. Deploy to one staging instance and request `/health` over HTTPS.

4. Confirm the response is `200` and the certificate expires on the approved date.

5. Roll out to production one instance at a time.

6. After all instances report the new fingerprint, remove the old certificate.

> If staging returns `495`, **stop the rollout** and compare the certificate chain with the approved record. Keep the current production certificate active while investigating.

The certificate renewal does not change the service hostname or client trust bundle.
