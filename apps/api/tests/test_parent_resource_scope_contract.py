from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding="utf-8")

def test_parent_scope_helper_is_tenant_and_relationship_bound():
    s=read("app/core/auth.py")
    assert "Guardian.user_id==user.id" in s
    assert "StudentGuardian.tenant_id==user.tenant_id" in s
    assert 'has_role(db,user,"PARENT")' in s
    assert 'status_code=404' in s

def test_parent_finance_is_linked_student_scoped():
    s=read("app/api/v1/finance.py")
    assert "linked_student_ids(db,u)" in s
    assert "Invoice.student_id.in_(ids)" in s
    assert "require_linked_student(db,u,inv.student_id)" in s

def test_parent_learning_courses_are_linked_enrollment_scoped():
    s=read("app/api/v1/learning.py")
    assert "Enrollment.student_id.in_(ids)" in s
    assert "Course.section_id.in_(section_ids)" in s
    assert "require_linked_student(db,u,p.student_id)" in s

def test_parent_seed_allows_scoped_payment_flow():
    s=read("app/scripts/seed.py")
    line=next(x for x in s.splitlines() if x.startswith("PARENT_PERMISSIONS="))
    assert '"finance.payment.record"' in line
