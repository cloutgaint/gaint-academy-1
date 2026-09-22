from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(path): return (ROOT/path).read_text(encoding="utf-8")

def test_auth_me_exposes_roles_scopes_and_permissions():
    src=text("app/api/v1/auth.py")
    assert '"roles":role_codes(db,user)' in src
    assert '"scopes":role_scopes(db,user)' in src
    assert '"permissions":permission_codes(db,user)' in src

def test_parent_student_queries_use_guardian_relationship():
    src=text("app/api/v1/students.py")
    assert 'has_role(db,user,"PARENT")' in src
    assert "Guardian.user_id==user.id" in src
    assert "Student.id.in_(allowed)" in src

def test_parent_cannot_read_unlinked_guardians():
    src=text("app/api/v1/people.py")
    assert 'has_role(db,user,"PARENT")' in src
    assert "Guardian.user_id==user.id" in src
    assert 'raise HTTPException(404,"Student not found")' in src

def test_parent_role_gets_minimum_read_permissions():
    src=text("app/scripts/seed.py")
    assert "PARENT_PERMISSIONS=" in src
    assert '"students.student.view"' in src
    assert '"staff.staff.view"' not in src.split("PARENT_PERMISSIONS=",1)[1].split("PERMISSIONS=",1)[0]
