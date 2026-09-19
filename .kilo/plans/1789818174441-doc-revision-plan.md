## Objective
- Review and revise the Bikita Minerals DWRMS project documentation suite to improve clarity, structure, professional tone, and internal consistency across all docs.

## Important Details
- Current platform version confirmed as `v2.10.0` in `backend/app/core/config.py` (APP_VERSION, DB_SCHEMA_VERSION="2026.08.28.01", API_VERSION="v1", MIN_SUPPORTED_CLIENT_VERSION="v2.0.0").
- Production standardizes on PostgreSQL 16 (`infrastructure/docker-compose.prod.yml`); a legacy `docker-compose.mysql.yml` with hardcoded credentials still exists.
- `DEPLOYMENT_MODE` is the correct env var name in `config.py`; root `.env` and `.env.example` incorrectly used `REMOTE_CONNECTIVITY_MODE`.
- 9 Alembic migration files exist in `backend/alembic/versions/`; docs claimed "12 revisions".
- 34 backend test files (18 root + 13 api + conftest + init).
- `install.sh` has 7 stages `[1/7]`–`[7/7]`; CROSS_PLATFORM_SETUP.md incorrectly listed 8 numbered steps.
- `ops logs` CLI supports both `-n`/`--lines` and `-f`/`--follow` flags (`backend/app/cli/logs.py:19-20`); INTERFACE_MODES.md correctly documents both forms.

## Work State
### Completed
- Verified version, schema version, migration count (9), test file count (34), dist/ artifacts, and env var names from source code.
- **Root `.env.example`**: removed contradictory `DB_PORT="5432"` for SQLite, removed hardcoded `SECRET_KEY`, renamed `REMOTE_CONNECTIVITY_MODE` → `DEPLOYMENT_MODE`, added missing variables (`REMOTE_CONNECTIVITY_ENABLED`, `REMOTE_NETWORK_PROVIDER`, `MIN_SUPPORTED_CLIENT_VERSION`, `UPDATE_CHANNEL`).
- **Root `.env`**: `REMOTE_CONNECTIVITY_MODE` → `DEPLOYMENT_MODE` (was ignored by config.py).
- **`docs/OPS_CLI_REFERENCE.md`**: `v2.2.0` → `v2.10.0` (3 locations), `MYSQL` → `PostgreSQL 16` (2 locations), `ops update` → `ops update matrix/check/apply/rollback`, removed MySQL from engine options and credential redaction list.
- **`docs/UBUNTU_SERVER_DEPLOYMENT.md`**: title `(V1.9)` → `(v2.10.0)`, `MySQL 8.0 or PostgreSQL 16` → `PostgreSQL 16`, fixed broken `file:///c:/...` link → relative path, JSON `"version": "v1.9.0"` → `"v2.10.0"`, `ops update` → `ops update apply`, `dwrms_prod` → `dwrms_user`.
- **`docs/SERVER_FIRST_ARCHITECTURE.md`**: `(V1.8)` → `(v2.10.0)`, `MySQL / PostgreSQL` → `PostgreSQL 16`, `MySQL 8.0 or PostgreSQL 16` → `PostgreSQL 16`.
- **`docs/SECURE_REMOTE_CONNECTIVITY.md`**: `Version 2.6` → `Version 2.10.0`, removed broken `file:///c:` link.
- **`deploy/.env.example`**: `V1.9` header → `v2.10.0`, `APP_VERSION=v1.9.0` → `v2.10.0`, removed MySQL from DB engine comment.
- **`deploy/.env.production.example`**: `APP_VERSION=v2.1.0` → `v2.10.0`, `IMAGE_TAG=v2.1.0` → `v2.10.0`, `DB_ENGINE=mysql` → `postgresql`, `DB_PORT=3306` → `5432`, `DB_USER=user` → `dwrms_user`, removed MySQL-specific vars (MYSQL_USER, MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD, MYSQL_DATABASE), comment `MySQL 8.0` → `PostgreSQL 16`.
- **`deploy/.env.staging.example`**: `APP_VERSION=v1.9.0-rc1` → `v2.10.0-rc1`.
- **`docs/DISASTER_RECOVERY.md`**: `Version 2.8` → `Version v2.10.0` (header + JSON `platform_version` field), `ops logs --lines 100 --follow` → `ops logs -n 100 -f`.
- **`docs/CROSS_PLATFORM_SETUP.md`**: merged 8th numbered step (Systemd Registration) into 7th stage to match `install.sh`'s `[7/7]` stage, changed Windows Native DB column `SQLite / MySQL` → `SQLite (local dev)`.
- **`docs/UPGRADE_AND_MIGRATION_GUIDE.md`**: "12 revisions" → "9 revisions", fixed typo in migration hash (`de bd9a6a4bcd` → `debd9a6a4bcd`).
- **`docs/SSH_SERVER_ADMINISTRATION.md`**: `Version 2.5` → `Version v2.10.0`, bare `ops update` → `ops update matrix`.
- **`docs/INTERFACE_MODES.md`**: `PostgreSQL/MySQL` → `PostgreSQL 16` in DB connection latency test description.

### Active
- (none)

### Blocked
- (none)

## Next Move
- Final grep verification complete — no stale version references remain in docs.
- Remaining MySQL references are all legitimate: GAP_ANALYSIS.md (documents the known gap), INSTALLATION_AND_DEPENDENCIES.md (lists actual `aiomysql` dependency in requirements.txt), CROSS_PLATFORM_SETUP.md UFW rule (valid security hardening), OPERATIONAL_READINESS_AUDIT.md (describes existing file audit status).

## Relevant Files
- `.kilo/plans/1789818174441-doc-revision-plan.md` — comprehensive revision plan (26 steps)
- `.env.example` — root dev env template (FIXED)
- `.env` — root dev env (FIXED: REMOTE_CONNECTIVITY_MODE → DEPLOYMENT_MODE)
- `backend/app/core/config.py` — authoritative version, DB engine, env var definitions
- `backend/app/cli/main.py:31,44,46` — `ops version` CLI output format (v2.10.0, POSTGRESQL)
- `backend/app/core/version.py` — PlatformVersionManager with version_matrix function
- `backend/app/cli/status.py:30` — `ops status` version output uses `settings.APP_VERSION`
- `backend/app/cli/logs.py:19-20` — confirms both `-n`/`--lines` and `-f`/`--follow` flags are valid
- `infrastructure/docker-compose.prod.yml` — production compose using postgres:16
- `infrastructure/docker-compose.mysql.yml` — legacy MySQL compose with hardcoded credentials (`MYSQL_PASSWORD: password`)
- `deploy/.env.example` — had `APP_VERSION=v1.9.0`, `V1.9` header (FIXED)
- `deploy/.env.production.example` — had `APP_VERSION=v2.1.0`, `DB_ENGINE=mysql`, MySQL-specific vars (FIXED)
- `deploy/.env.staging.example` — had `APP_VERSION=v1.9.0-rc1` (FIXED)
- `backend/alembic/versions/` — 9 migration files (docs claimed 12)
