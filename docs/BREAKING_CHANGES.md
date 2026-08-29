# Breaking Change Notes & Client Compatibility Policy

## Version 2.9.0 Compatibility Guidelines

### 1. Client Compatibility Threshold
* **Minimum Supported Client Version**: `v2.0.0`
* **Current Authoritative Version**: `v2.9.0`
* Any legacy desktop client older than `v2.0.0` connecting to the platform API will receive a compatibility warning or be rejected during authentication handshake.

### 2. Idempotency Header Requirement
* Mutating endpoints (`POST /api/v1/job-cards`, `POST /api/v1/fleet/requisitions`, `POST /api/v1/approvals`) strongly recommend attaching `X-Idempotency-Key`.
* Unrecognized retransmissions with duplicate idempotency keys return HTTP 200/201 with `X-Idempotency-Replay: true` instead of creating duplicate records.

### 3. Deprecations
* Raw untagged backup archives are deprecated in favor of standardized archives bearing `manifest.json`.
