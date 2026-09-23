# GAINT Academy v1.1 Release Candidate

## Status
Release-candidate documentation only. This does not authorize production deployment.

## v1.1 scope completed
- Role-aware dashboards for Admin, Parent, Student, Teacher, Accounts, HR, Campus Admin and Auditor.
- Parent linked-child resource scope for students, learning, attendance, finance, reports and dashboard metrics.
- Student self-scope for student records, learning, attendance, finance/report visibility and dashboard metrics.
- Teacher STAFF-scope identity binding and assigned-section authorization.
- Least-privilege operational roles for ACCOUNTS, HR, CAMPUS_ADMIN and AUDITOR.
- Notice audience validation, role-aware visibility and targeted notification fan-out.
- Login brute-force protection backed by Redis.
- CSRF protection for cookie-authenticated mutations.
- Payment initiation separated from direct payment-record permission.
- Payment webhook lookup bound to tenant_id + provider + provider_order_id.
- DB-backed PostgreSQL tenant-isolation and IDOR tests in CI.
- Frontend typed API errors, recoverable error states and global 404 handling.

## Required release evidence
The candidate is acceptable for UAT only when:
1. API compile and test jobs pass.
2. PostgreSQL migrations reach Alembic head.
3. DB-backed tenant/IDOR integration tests pass.
4. Next.js build passes.
5. npm audit --audit-level=high passes.
6. The v1.1 UAT checklist is executed against the intended UAT environment.

## Known non-v1.1 / deferred work
- Real AI provider, RAG, governed tool execution and AI evaluation suite.
- Provider-specific payment adapters, reconciliation, refunds and maker-checker workflows.
- Full external messaging adapters/outbox.
- Native mobile applications.
- Advanced campus modules and production SSO/MFA.
- Broader Playwright E2E/performance coverage beyond the current CI security/integration gates.

## Deployment sequence
Local Windows validation → UAT/staging → defect remediation/retest → pilot approval → server deployment.

Do not deploy directly from an untested developer workstation or bypass UAT.
