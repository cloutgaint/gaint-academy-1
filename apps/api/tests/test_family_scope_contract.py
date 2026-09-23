from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_fee_plan_contract_stays_fee_plan_only():
 s=read("app/api/v1/finance.py")
 block=s[s.index('@router.get("/fee-plans")'):s.index('class InvoiceIn')]
 assert "select(FeePlan)" in block
 assert '@router.get("/invoices")' in block
 assert "linked_student_ids" in block
 assert "scoped_student_id" in block

def test_payment_initiation_is_separate_from_recording():
 s=read("app/api/v1/finance.py")
 assert 'req(db,u,"finance.payment.record")' in s
 assert 'req(db,u,"finance.payment.initiate")' in s
 assert "require_linked_student(db,u,inv.student_id)" in s
 assert "require_self_student(db,u,inv.student_id)" in s

def test_parent_does_not_get_direct_payment_record_permission():
 s=read("app/scripts/seed.py")
 parent=next(x for x in s.splitlines() if x.startswith("PARENT_PERMISSIONS="))
 assert '"finance.payment.initiate"' in parent
 assert '"finance.payment.record"' not in parent

def test_attendance_history_is_family_and_student_scoped():
 s=read("app/api/v1/attendance.py")
 assert '@router.get("/attendance/records")' in s
 assert 'has_role(db,u,"PARENT")' in s
 assert 'has_role(db,u,"STUDENT")' in s
 assert "AttendanceSession.status==\"SUBMITTED\"" in s
