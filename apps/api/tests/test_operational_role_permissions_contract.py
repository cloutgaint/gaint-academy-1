from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_operational_roles_are_seeded_with_least_privilege_sets():
 s=read("app/scripts/seed.py")
 for name in ["ACCOUNTS_PERMISSIONS","HR_PERMISSIONS","CAMPUS_ADMIN_PERMISSIONS","AUDITOR_PERMISSIONS"]:
  assert name in s
 assert '"finance.payment.record"' in s[s.index("ACCOUNTS_PERMISSIONS"):s.index("HR_PERMISSIONS")]
 assert '"finance.payment.record"' not in s[s.index("HR_PERMISSIONS"):s.index("CAMPUS_ADMIN_PERMISSIONS")]
 assert '"finance.payment.record"' not in s[s.index("CAMPUS_ADMIN_PERMISSIONS"):s.index("AUDITOR_PERMISSIONS")]
 auditor=s[s.index("AUDITOR_PERMISSIONS"):s.index("\nPERMISSIONS=",s.index("AUDITOR_PERMISSIONS"))]
 assert '"audit.event.view"' in auditor

def test_hr_and_campus_admin_do_not_receive_reports_by_default():
 s=read("app/scripts/seed.py")
 hr=s[s.index("HR_PERMISSIONS"):s.index("CAMPUS_ADMIN_PERMISSIONS")]
 campus=s[s.index("CAMPUS_ADMIN_PERMISSIONS"):s.index("AUDITOR_PERMISSIONS")]
 assert '"reports.summary.view"' not in hr
 assert '"reports.summary.view"' not in campus

def test_campus_admin_dashboard_avoids_finance_metric():
 s=read("app/api/v1/dashboard.py")
 block=s[s.index('elif "CAMPUS_ADMIN" in roles:'):s.index('elif "AUDITOR" in roles:')]
 assert '"Open invoices"' not in block
 assert '"/campus"' in block
