from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding="utf-8")

def test_student_scope_is_bound_to_student_role_scope():
    s=read("app/core/auth.py")
    assert 'scope["role"]=="STUDENT"' in s
    assert 'scope["scope_type"]=="STUDENT"' in s
    assert "scoped_student_id(db,user)!=student_id" in s
    assert "Enrollment.tenant_id==user.tenant_id" in s

def test_student_directory_is_self_scoped():
    s=read("app/api/v1/students.py")
    assert 'has_role(db,user,"STUDENT")' in s
    assert "q=q.where(Student.id==own)" in s
    assert "require_self_student(db,user,student_id)" in s

def test_student_account_creation_binds_resource_scope():
    s=read("app/api/v1/students.py")
    assert '@router.post("/{student_id}/student-account",status_code=201)' in s
    assert 'scope_type="STUDENT"' in s
    assert 'scope_id=str(student.id)' in s

def test_learning_is_self_scoped():
    s=read("app/api/v1/learning.py")
    assert 'has_role(db,u,"STUDENT")' in s
    assert "student_section_ids(db,u)" in s
    assert "require_self_student(db,u,p.student_id)" in s

def test_student_permissions_seeded():
    s=read("app/scripts/seed.py")
    line=next(x for x in s.splitlines() if x.startswith("STUDENT_PERMISSIONS="))
    for permission in ["students.student.view","learning.course.view","learning.submission.create"]:
        assert f'"{permission}"' in line
