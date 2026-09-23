# GAINT Academy v1.1 UAT Checklist

## Release gate
Do not approve pilot deployment until every P0 item passes in the target UAT environment. CI success is required but does not replace manual UAT.

## P0 identity and session security
- [ ] Institution-code login succeeds only for the correct active tenant.
- [ ] Five repeated failed login attempts trigger the configured rate limit.
- [ ] Successful login clears the failed-login counter.
- [ ] Authenticated state-changing requests require a valid CSRF token.
- [ ] Logout revokes the current session and clears session/CSRF cookies.
- [ ] Password reset OTP expires, throttles resend, limits attempts and revokes active sessions after reset.
- [ ] Change password revokes other active sessions.
- [ ] No default or shared production administrator password is present.

## P0 tenant and resource authorization
- [ ] Cross-tenant student IDs return 404 and never disclose foreign data.
- [ ] Parent can view only explicitly linked children.
- [ ] Student can view only the scoped Student record.
- [ ] Teacher can act only on assigned sections through STAFF scope.
- [ ] Teacher account creation binds TEACHER → STAFF scope.
- [ ] Parent attendance, finance, reports and dashboard metrics are limited to linked children.
- [ ] Student attendance, learning, reports and dashboard metrics are limited to self.
- [ ] Teacher reports and dashboard metrics are limited to assigned sections and do not expose finance.
- [ ] ACCOUNTS, HR, CAMPUS_ADMIN and AUDITOR permission sets remain least-privilege.
- [ ] Auditor workflow remains read-only for pilot scope.

## P0 academics and attendance
- [ ] Institution Admin can create academic year, class, section, student, guardian and staff.
- [ ] Enrollment rejects resources from another tenant.
- [ ] Timetable read/write permissions are enforced.
- [ ] Attendance cannot submit until the required roster state is complete.
- [ ] Parent/Student attendance history exposes only SUBMITTED sessions.
- [ ] Submitted absences notify only explicitly linked guardian users.

## P0 learning
- [ ] Student course list is limited to active enrolled sections.
- [ ] Student assignment submission cannot impersonate another student.
- [ ] Parent course visibility is limited to linked-child enrollment.
- [ ] Teacher course/assignment/assessment operations are limited to assigned sections.
- [ ] Assessment publication remains a controlled state transition and is audited.

## P0 finance
- [ ] Fee plans retain consistent response semantics for every role.
- [ ] Parent/Student invoice lists are resource-scoped.
- [ ] Parent/Student use finance.payment.initiate rather than direct payment-record permission.
- [ ] Direct confirmed payment recording is restricted to authorized finance/admin roles.
- [ ] Duplicate payment-order idempotency keys do not create duplicate orders.
- [ ] Invalid payment webhook signatures are rejected.
- [ ] Payment webhook lookup is bound to tenant_id + provider + provider_order_id.
- [ ] Replayed confirmed payment references do not duplicate payments.
- [ ] Confirmed webhook processing creates audit evidence.

## P0 communication
- [ ] Notice audience accepts only ALL, STUDENT, PARENT, TEACHER or STAFF.
- [ ] Notice list shows only audiences visible to the current role.
- [ ] Targeted notice publish fan-out does not notify unrelated tenant users.
- [ ] Notification read/update is restricted to the current user.

## P0 platform and frontend
- [ ] Permission-driven navigation hides inaccessible modules.
- [ ] Role dashboards show only role-appropriate KPIs.
- [ ] 401 responses redirect to login; 403/404/server errors do not masquerade as logout.
- [ ] Global 404 and recoverable error screens render correctly.
- [ ] Responsive UAT passes at desktop, tablet and mobile widths.
- [ ] /health/live and /health/ready return healthy status.
- [ ] Alembic upgrade head succeeds against a clean PostgreSQL database.
- [ ] PostgreSQL-backed tenant/IDOR tests pass in CI.
- [ ] Web build and npm audit --audit-level=high pass.

## P0 AI boundary
- [ ] AI remains SAFE_PLACEHOLDER unless an approved provider/retrieval adapter is configured.
- [ ] AI action confirmation reports executed=false.
- [ ] No AI path can bypass normal API authorization or tenant scope.

## UAT evidence
For every P0 item record: tester, environment, date/time, role, tenant, test-data IDs, expected result, actual result, PASS/FAIL, screenshot/log reference, defect link and retest result.

## Pilot decision
Pilot approval requires:
- zero open P0 defects;
- CI green on the release-candidate commit;
- database migration verification complete;
- security/tenant isolation retest complete;
- backup/restore rehearsal completed in a disposable environment;
- all remaining P1 defects assigned an owner, workaround and remediation date.
