# GAINT Academy

AI-powered unified education and campus management platform.

## v1.1 Release Candidate

Stack:
- Next.js + TypeScript
- FastAPI + SQLAlchemy + Alembic
- PostgreSQL
- Redis
- MinIO / S3-compatible object storage
- Docker Compose
- Tenant-aware RBAC, secure sessions and audit

Seed administrator: `gaintclout@gmail.com`

## Windows quick start

Requirements: Git, Docker Desktop with Docker Compose.

1. Clone/pull the repository and open PowerShell in the repository root.
2. Create local environment file:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Open `.env` and replace every `change-me-...` value, especially:
   ```env
   POSTGRES_PASSWORD=<your-local-db-password>
   DATABASE_URL=postgresql+psycopg://gaint:<same-password>@postgres:5432/gaint_academy
   MINIO_SECRET_KEY=<your-local-minio-password>
   SEED_ADMIN_PASSWORD=<your-development-admin-password>
   ```
   Do not commit `.env`.
4. Start:
   ```powershell
   docker compose up --build
   ```
   The API container automatically runs Alembic migrations and the idempotent development seed before Uvicorn.
5. Verify:
   - Web: http://localhost:3000
   - Login: http://localhost:3000/login
   - API docs: http://localhost:8000/docs
   - Live: http://localhost:8000/health/live
   - Ready: http://localhost:8000/health/ready
   - MinIO console: http://localhost:9001
6. Login with `gaintclout@gmail.com` and the value you set for `SEED_ADMIN_PASSWORD`.

## Useful commands

```powershell
docker compose ps
docker compose logs -f api
docker compose logs -f web
docker compose down
docker compose down -v
```

Use `docker compose down -v` only when you intentionally want to delete local PostgreSQL and MinIO data.

## Security

No real administrator password or production secret is committed. Sessions use random opaque tokens; only token hashes are stored in PostgreSQL and the browser receives an HttpOnly cookie. Tenant and permission context are resolved server-side.

## Development sequence

Foundation → Core Modules → Authorization Hardening → Security/UX Stabilization → v1.1 UAT → Pilot → Production.


## v1.1 release documents

- UAT gate: `docs/UAT_CHECKLIST.md`
- Release candidate notes: `docs/RELEASE_NOTES_v1.1_RC.md`

The current release candidate is for local/UAT validation only. Production deployment requires the full P0 UAT gate to pass.
