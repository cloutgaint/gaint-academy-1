from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_student_dashboard_attendance_uses_self_identity():
 s=read("app/api/v1/dashboard.py")
 assert "own=scoped_student_id(db,user)" in s
 assert "AttendanceRecord.student_id==own" in s

def test_student_attendance_kpi_only_counts_submitted_sessions():
 s=read("app/api/v1/dashboard.py")
 student=s[s.index("if student_role:"):s.index('elif parent:')]
 assert 'AttendanceSession.status=="SUBMITTED"' in student
 assert 'AttendanceRecord.status=="PRESENT"' in student

def test_student_attendance_rate_handles_no_records():
 s=read("app/api/v1/dashboard.py")
 assert 'attendance_rate="—" if not submitted' in s
 assert 'round((present/submitted)*100)' in s
