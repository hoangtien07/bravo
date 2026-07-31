# WP-00 provider-credential rotation attestation

Status: `PENDING OWNER SIGNATURE`

This control intentionally records neither a credential nor any portion of one. Complete it only
after rotating the provider credential in the provider control plane and injecting the replacement
through the approved secret source.

| Field | Owner entry |
| --- | --- |
| Provider / project | OpenAI / ____________________ |
| Replacement credential identifier or secret version | ____________________ |
| Rotation completed (UTC) | ____________________ |
| Previous credential revoked | `YES / NO` |
| Secret source updated for `.env.wp00` or deployment | `YES / NO` |
| Operator name and signature | ____________________ |

The signer confirms that no value from the revoked credential is stored in Git, evidence, logs, or
this attestation. `YES` is required for every boolean field before WP-00 can pass.
