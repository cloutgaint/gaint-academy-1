from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def parent_block():
 s=read("app/api/v1/dashboard.py")
 return s[s.index("elif parent:"):s.index('elif "TEACHER" in roles:')]

def test_parent_attendance_kpi_is_linked_child_scoped():
 s=parent_block()
 assert "AttendanceRecord.student_id.in_(linked)" in s
 assert 'AttendanceSession.status=="SUBMITTED"' in s
 assert 'AttendanceRecord.status=="PRESENT"' in s

def test_parent_notice_kpi_matches_visible_audiences():
 s=parent_block()
 assert 'Notice.audience.in_({"ALL","PARENT"})' in s
 assert '"Published notices","value":visible_notice_count' in s

def test_parent_dashboard_handles_no_attendance():
 s=parent_block()
 assert 'attendance_rate="—" if not attendance_total' in s
