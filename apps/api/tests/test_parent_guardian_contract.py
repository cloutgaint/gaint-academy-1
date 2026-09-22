from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def text(path):
    return (ROOT/path).read_text(encoding="utf-8")

def test_parent_account_is_tenant_scoped_and_role_bound():
    src=text("app/api/v1/people.py")
    assert 'Guardian.tenant_id==user.tenant_id' in src
    assert 'Role.tenant_id==user.tenant_id,Role.code=="PARENT"' in src
    assert 'scope_type="GUARDIAN"' in src
    assert 'require(db,user,"users.user.create")' in src

def test_guardian_listing_is_student_and_tenant_scoped():
    src=text("app/api/v1/people.py")
    assert '@router.get("/students/{student_id}/guardians")' in src
    assert 'StudentGuardian.student_id==student.id' in src
    assert 'StudentGuardian.tenant_id==user.tenant_id' in src
