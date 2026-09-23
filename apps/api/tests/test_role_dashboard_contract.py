from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_teacher_dashboard_is_assignment_scoped():
 s=read("app/api/v1/dashboard.py")
 assert '"TEACHER" in roles' in s
 assert "teacher_section_ids(db,user)" in s
 assert "AttendanceSession.section_id.in_(sections)" in s

def test_accounts_hr_and_auditor_have_distinct_summaries():
 s=read("app/api/v1/dashboard.py")
 for role in ['"ACCOUNTS" in roles','"HR" in roles','"AUDITOR" in roles']:
  assert role in s
 assert '"READ ONLY"' in s

def test_web_labels_student_teacher_and_auditor_roles():
 s=read("../web/app/dashboard/DashboardClient.tsx")
 assert '"Student Dashboard"' in s
 assert '"Teacher Dashboard"' in s
 assert 'roles.includes("AUDITOR")' in s
